---
type: Concept
title: Virtual Optimizer（优化器显存虚拟化）
description: Virtual Optimizer（torchtitan-npu）：基于 Ascend NPU 原生虚拟内存映射卸载 AdamW 一二阶动量 exp_avg/exp_avg_sq——内存在 Host、地址可映射 Device 仍可参与多数 NPU 算子，'不改训练代码'省显存。核心 torch_npu.empty_with_swapped_memory 替代 torch.zeros_like 的 NPU 显存分配。派生自 MindSpeed VirtualOptimizer，要求 NPU 驱动 25.5.2+。配置 OptimizerConfig.virtual_optimizer(bool)/virtual_optimizer_size('all' 卸全部)。与 swap_optimizer 互斥。区别 swap-optimizer（三流水手动 H2D/D2H+resize_(0)）：virtual 是地址映射、对代码透明。V4 285B 续训实采 virtual_optimizer=true。 MindSpeed 原生 VirtualOptimizerFeature 用 torch_npu.empty_with_swapped_memory 把 AdamW 动量 exp_avg/exp_avg_sq 放 Host、按 PP stage 逐张量字节预算（--virtual-optimizer all/标量/list）映射 Device，与 fused_ema_adamw 互斥。
tags:
- task.optimization
- topic.memory
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/virtual_optimizer.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Virtual Optimizer（优化器显存虚拟化）

## Summary

Virtual Optimizer 是 torchtitan-npu 提供的一套**基于 Ascend NPU 原生虚拟内存能力**的优化器显存优化方案。它把 AdamW 优化器的一阶/二阶动量（`exp_avg`、`exp_avg_sq`）实际存储在 **Host（CPU）内存**中，但其地址被映射到 Device，使得张量仍可参与大多数 NPU 算子计算——**在不修改任何训练代码的前提下**节省 NPU 显存占用。该实现派生自 MindSpeed 的 [VirtualOptimizer 特性](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/docs/zh/features/virtual-optimizer.md)。

与 [swap-optimizer](swap_optimizer.md)（手动三流 H2D/D2H 拷贝 + 切片 `resize_(0)` 的流水化 swap）不同，Virtual Optimizer 走的是**地址映射、代码透明**的路线：动量张量的内存物理上常驻 Host，但对训练代码而言其使用方式与普通 NPU 张量无异。

> 需要 **NPU 驱动 25.5.2 及以上版本**（`torch_npu.empty_with_swapped_memory` 依赖）。

## 背景与动机

在大集群训练中，增大 PP（流水线并行）会对前几个 stage 造成较大显存压力。同时观察到：在**梯度累积较大**的情况下，优化器一二阶动量的显存 swap 开销可忽略不计。因此可将优化器动量 swap 到 CPU 以节省整网显存。而当前分布式优化器逻辑复杂、与各类通信并行相互耦合，手写一套 swap 系统较为复杂——Virtual Optimizer 借助驱动级虚拟内存能力规避了这一复杂度。

## 核心实现原理

标准 `torch.optim.AdamW` 在 NPU 显存中直接分配动量状态：

```python
# torch.optim.AdamW（标准实现）：直接在 NPU 显存分配
state['exp_avg']    = torch.zeros_like(p, memory_format=torch.preserve_format)
state['exp_avg_sq'] = torch.zeros_like(p, memory_format=torch.preserve_format)
```

Virtual Optimizer 用虚拟内存分配替代上述 NPU 显存分配——核心在 `VirtualAllocator._get_swap_memory`：

```python
# virtual_optimizer.py：实际内存在 Host，地址映射到 Device
swap_tensor = torch_npu.empty_with_swapped_memory(p.size(), device=p.device)
swap_tensor.swap_tensor = True
swap_tensor.data.swap_tensor = True
swap_tensor.zero_()
```

关键设计点（均来自 `torchtitan_npu/patches/optimizer/virtual_optimizer.py`）：

- **状态键**：`OPTIMIZER_STATE_KEYS = ["exp_avg", "exp_avg_sq", "max_exp_avg_sq"]`；`exp_avg`/`exp_avg_sq` 走 swap 分配，`max_exp_avg_sq`（amsgrad）仍用 `torch.zeros_like` 常驻 HBM。
- **swap 标记**：被换出的张量打上 `swap_tensor=True` 属性；为保证 `copy_` / `cpu` / `clone` / `detach` 等张量方法能正确传播该标记，框架对这些方法做了 wrapper patch（见 `optimizer_selector.py` 的 `_apply_virtual_patch`）。
- **DTensor 兼容**：分配出的 local tensor 通过 `wrap_like_param` 用 `DTensor.from_local` 还原成与参数同 `device_mesh`/`placements` 的 DTensor，保证与 FSDP/TP 等并行兼容。
- **优雅降级**：若 `torch_npu` 不具备 `empty_with_swapped_memory`，或 swap 分配抛异常，则 `fallback` 回 `torch.zeros_like` 的标准 HBM 分配（不致训练失败）。
- **step 改写**：通过 `virtual_optimizer_step` 替换 `Adam/AdamW.step`，复用 `torch._fused_adamw_` / `torch._fused_adam_` 融合 kernel 完成更新。
- **checkpoint 处理（非透明，承重）**：`_apply_virtual_patch` 在替换 `step` 的同时一并改写 `state_dict` 与 `load_state_dict`。保存时 `patched_state_dict` 经 `_save_original_states` / `_process_state_tensor` 把 swap 动量 `.cpu().clone()` 搬回 CPU 普通张量（DTensor 则按原 `device_mesh`/`placements` 重建 `DTensorSpec`），存盘后再 `_restore_original_states` 还原内存中的 swap 状态；加载时 `_make_patched_load` 在原始 `load_state_dict` 之后调用 `virtual_optimizer_replace`，经 `virtual_allocator.create` 为每个动量重新分配 swap 内存，恢复「Host 常驻、Device 可寻址」。即 Virtual Optimizer 对 checkpoint 并非透明，需专门转换。

## 配置选项

由 `torchtitan_npu.config.configs.OptimizerConfig` 的字段配置（在各模型 `config_registry.py` 中设置）：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `virtual_optimizer` | bool | `False` | 是否启用 Virtual Optimizer 以卸载动量显存。 |
| `virtual_optimizer_size` | float / list[float] / str / None | `None` | 各 PP stage 申请的虚拟内存大小。`'all'` 表示 swap 掉全部一二阶动量；单个数值表示各 stage 统一大小；list 表示逐 stage 指定。 |

`virtual_optimizer_size` 的解析逻辑（`VirtualAllocator.get_swap_memory_sizes`）：`'all'` → 每个 PP stage `65.0` GB；标量 → 每 stage 该值；长度为 1 的 list → 广播到所有 stage；长度等于 `pp_stages` 的 list → 逐 stage；否则抛 `ValueError`。

> ⚠️ `virtual_optimizer` 与 `swap_optimizer` **互斥**：`NpuOptimizerDispatcher.dispatch_build` 在两者同时为 `True` 时抛 `ValueError("Cannot enable both virtual_optimizer and swap_optimizer at the same time.")`。

### 配置示例

```python
from torchtitan_npu.config.configs import OptimizerConfig

optimizer = OptimizerConfig(
    name="AdamW",
    lr=3e-4,
    weight_decay=0.01,
    virtual_optimizer=True,
    virtual_optimizer_size="all",
)
```

启动时也可通过命令行覆盖同名字段：

```bash
bash scripts/run_train.sh \
  --optimizer.virtual_optimizer \
  --optimizer.virtual_optimizer_size all
```

## 适用场景与对比

**适用场景**：大集群 PP 训练中前序 stage 显存吃紧、且梯度累积较大（此时动量 swap 的拷贝开销可忽略）。透明无侵入，无需改训练代码。

| 维度 | Virtual Optimizer | [swap-optimizer](swap_optimizer.md) |
| --- | --- | --- |
| 机制 | 驱动级虚拟内存地址映射（Host 常驻、Device 可寻址） | 手动三流 H2D/D2H 拷贝 + 切片 `resize_(0)` 流水化 |
| 代码侵入 | 透明，无需改训练代码 | 改写 `step`，按 `swap_optimizer_times` 切片调度 |
| 驱动依赖 | NPU 驱动 25.5.2+ | 无该特定驱动要求 |
| 互斥 | 与 swap_optimizer 互斥 | 与 virtual_optimizer 互斥 |

实践选型：现有 DeepSeek 实践均**未启用** Virtual Optimizer——[deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（V4 285B 续训）与 DeepSeek-V3.2 预训练的主力 4k 配置都走互斥的 `swap_optimizer=true`（SwapOptimizer）路线；后者是同一分发器内面向「显存吃紧 + 梯度累积大」PP 场景的透明替代项。Virtual Optimizer 由 `NpuOptimizerDispatcher.dispatch_build` 在 virtual / swap / standard 三个分支间分发；而 [muon-optimizer](muon_optimizer.md) 走的是**独立路径**——经由 `MuonHybridOptimizersContainer.Config.build()`（校验 `name == "Muon"`）构建，**不经过 `NpuOptimizerDispatcher`**。`virtual_optimizer` 与 `swap_optimizer` 才是该分发器内的互斥选项。

其思路与推理侧的 [kvcache-offload](../../../inference/concepts/techniques/kvcache_offload.md)（把 KV cache 卸载到 Host 内存换取显存）相通——都是用 Host 内存换 Device 显存，区别在于 Virtual Optimizer 依靠驱动虚拟内存映射做到对算子透明。

## MindSpeed 原生实现

torchtitan-npu 侧的 Virtual Optimizer 派生自 [mindspeed](../frameworks/mindspeed.md) 的 `virtual-optimizer` 特性，机制同源——都靠昇腾驱动的虚拟内存能力把 `exp_avg`/`exp_avg_sq` 的实际内存放在 Host、地址映射到 Device。差异在于 MindSpeed 跑在 Megatron-LM 栈上：动量是普通 FP32 张量（无 DTensor 包装），分配粒度与 checkpoint 适配走的是另一套代码。

### 特性开关与约束

`VirtualOptimizerFeature` 注册 CLI `--virtual-optimizer`，`nargs='+'` 收一串值，逐值经 `parse_list_for_virtual_optimizer`：`'all'` 解析为 `65.0`（源码注释「Maximum NPU memory」，单位 GB），否则 `float(value)`。三种用法：

- `--virtual-optimizer all` → 每个 PP stage 给 65 GB 预算（实质换出全部一二阶动量）；
- `--virtual-optimizer 2.0` → 每个 stage 统一 2 GB；
- `--virtual-optimizer 6 5 4 3` → 四个 stage 逐个 6/5/4/3 GB。

`validate_args` 两道校验：`torch_npu` 必须有 `empty_with_swapped_memory`，否则 `AssertionError` 提示升级 PTA；并 `incompatible_check(args, "fused_ema_adamw")`——**与 `fused_ema_adamw` 互斥**（排他对象与 torchtitan 侧「与 swap_optimizer 互斥」不同）。

### 按 PP stage 的字节预算分配

torchtitan 把 swap 大小当配置元数据，MindSpeed 则用 `VirtualAllocator` 把它实现成**逐张量消耗的字节预算**。`get_global_virtual_allocator` 惰性按 `(pp_rank, pp_world_size, args.virtual_optimizer)` 建一个全局 allocator 缓存到 `args` 上；`swap_size_this_pp_rank = get_swap_memory_size()[pp_rank] * 1024**3`（GB→字节）。`get_swap_memory_size` 的广播规则：长度为 1 → 广播到所有 stage；长度等于 `pp_stages` → 逐 stage；否则 `ValueError`；`None` → 全 0。

每个动量经 `create(p)` 分配，按预算余额二选一：

```python
def create(self, p):
    if self.swap_size_this_pp_rank > 0:
        return self.get_swap_memory(p)   # 虚拟内存：Host 常驻、Device 可寻址
    else:
        return self.get_npu_memory(p)    # 预算耗尽 → 退回 HBM zeros_like
# virtual_adam.py — VirtualAllocator.create
```

`get_swap_memory` 调 `torch_npu.empty_with_swapped_memory(p.size(), device=p.device)`，给 tensor 及其 `.data` 都打 `swap_tensor=True`、`zero_()` 后把本张量字节数从预算扣除、累加到 `actually_swap_size`（MB，按 rank 打印汇总）。一旦该 stage 预算用尽、或 `empty_with_swapped_memory` 缺失、或分配抛异常，都**回退到 `torch.zeros_like` 的 HBM 分配**——即预算决定「换出多少动量」，超出部分仍留显存、不致训练失败。这正与 torchtitan 侧「`'all'`→65GB／标量逐 stage／list 逐 stage」语义同源。

### step 与更新算子

被 patch 的 `AdamW.step`（同时打 `mindspeed.optimizer.adamw` 与 `mindspeed.core.optimizer.adamw` 两处）走 `virtual_optimizer_step` → `virtual_optimizer_step_impl`：标准 AdamW 主循环，唯一改动是状态初始化处 `state['exp_avg'], state['exp_avg_sq'] = self.virtual_allocator.init_exp(p)`（虚拟还是 HBM 由预算决定）；amsgrad 的 `max_exp_avg_sq` 仍 `torch.zeros_like(p)` 常驻 HBM。更新调 `mindspeed.optimizer.adamw.adamw` 函数式接口，内部最终落到 `torch._fused_adamw_` 融合 kernel——与 torchtitan 侧、[swap-optimizer](swap_optimizer.md) 三者的更新算子一致。

### checkpoint 适配

虚拟内存张量没有随路计算单元、无法被直接拷贝/打印/保存，MindSpeed 用两层 patch 兜底：

- **全局张量方法 wrapper**：把 `torch.Tensor.{copy_, cpu, clone, npu, detach}` 换成 swap 感知版本。`swap_tensor_copy_wrapper` 对 swap 张量的同设备拷贝改用 `dst.fill_(1).mul_(src)`（乘法有计算通路）而非直接 `copy_`；`cpu`/`clone`/`npu` 经 `empty_like`+`copy_` 中转取出真值；`detach` 透传 `swap_tensor` 标记。
- **加载回链**：`replace_swap_tensor_wrapper` 包住 Megatron `DistributedOptimizer.load_parameter_state_from_dp_zero{,_legacy}` 与 `Float16OptimizerWithFloat16Params.load_state_dict`，在原加载完成后调 `virtual_optimizer_replace`，对每个 param 的 `exp_avg`/`exp_avg_sq` 做 `copy2swap`——重新申请虚拟内存并把加载值灌入，恢复「Host 真值、Device 可寻址」。

### 与多流 swap 的取舍

MindSpeed 文档给出虚拟内存相对手动多流 swap（即 [swap-optimizer](swap_optimizer.md) 那条路线）的取舍：虚拟内存省掉两次 UB↔HBM 搬运、直接由算子自身流水（MTE2/MTE3/Vector）做指令级并行掩盖，免去多流引入的流同步与额外显存开销；代价是 Host 虚拟内存**无随路计算**，涉及随路计算的算子用不了。文档推荐配 `CPU_AFFINITY_CONF=1,lazy_bind:0` 粗粒度绑核，把任务绑到 NPU 对应 NUMA 核、规避跨 NUMA 访问。环境依赖 Driver 25.0.RC1 / CANN 8.1.RC1 / PTA（2025 Q2 商发）。

## Evidence

- 特性文档：[`docs/feature_guides/virtual_optimizer.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/virtual_optimizer.md)
- 实现：[`virtual_optimizer.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/patches/optimizer/virtual_optimizer.py)（`VirtualAllocator._get_swap_memory` / `virtual_optimizer_step_impl`）
- 分发与 patch：[`optimizer_selector.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/patches/optimizer/optimizer_selector.py)（`NpuOptimizerDispatcher` 互斥校验、`_apply_virtual_patch`）
- 配置字段：[`configs.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/config/configs.py)（`OptimizerConfig.virtual_optimizer` / `virtual_optimizer_size`）
- 派生上游：MindSpeed VirtualOptimizer（`mindspeed/core/optimizer/virtual_optimizer/virtual_adam.py`）

MindSpeed 原生实现（@1432cb0）：

- 特性注册 / CLI / 校验：[`features_manager/optimizer/virtual_optimizer.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/optimizer/virtual_optimizer.py)（`VirtualOptimizerFeature`、`parse_list_for_virtual_optimizer` 的 `'all'`→65.0、`register_patches`、与 `fused_ema_adamw` 互斥）
- 分配器与 step：[`core/optimizer/virtual_optimizer/virtual_adam.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/optimizer/virtual_optimizer/virtual_adam.py)（`VirtualAllocator.create` / `get_swap_memory` / `get_swap_memory_size`、`virtual_optimizer_step_impl`、`virtual_optimizer_replace`）
- patch 入口：[`core/optimizer/virtual_optimizer/adaptor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/optimizer/virtual_optimizer/adaptor.py)（`virtual_optimizer_step`、`get_global_virtual_allocator`、`replace_swap_tensor_wrapper`）
- 融合更新：[`mindspeed/optimizer/adamw.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/optimizer/adamw.py)（函数式 `adamw` → `torch._fused_adamw_`）
- 官方文档：[`docs/zh/features/virtual-optimizer.md`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/docs/zh/features/virtual-optimizer.md)（背景、一行改造、虚拟内存 vs swap 取舍、绑核与环境依赖）

## Links

- [swap-optimizer](swap_optimizer.md) — 互斥的另一条优化器显存卸载路线（手动流水化 swap）
- [muon-optimizer](muon_optimizer.md) — 同在 `OptimizerConfig` 中配置的优化器选项
- [torchtitan](../frameworks/torchtitan.md) — 本特性所在训练框架
- [mindspeed](../frameworks/mindspeed.md) — VirtualOptimizer 的派生上游框架
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md) — 与本特性互斥的 `swap_optimizer=true` 实践（其 4k 主配置未启用 Virtual Optimizer）
- [kvcache-offload](../../../inference/concepts/techniques/kvcache_offload.md) — 推理侧同类「Host 内存换 Device 显存」思路
- [optimizer-memory](optimizer_memory.md)（同属优化器显存优化族：reuse-fp32-param / 低精度优化器 / LayerZeRO）
