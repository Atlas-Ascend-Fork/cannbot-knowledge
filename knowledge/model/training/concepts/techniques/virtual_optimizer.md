---
type: Concept
title: Virtual Optimizer（优化器显存虚拟化）
description: 当前 TorchTitan virtual override 的 Host-backed moments、DTensor 空分片、fresh-load destinations 与同步 DCP writer 边界，并区分 MindSpeed 的按 PP stage 预算实现。
tags:
- task.optimization
- topic.memory
- topic.optimizer
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/virtual_optimizer.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/optimizer.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/virtual-optimizer.md
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/virtual_optimizer/virtual_adam.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/virtual_optimizer/adaptor.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/optimizer/virtual_optimizer.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- a3
---

# Virtual Optimizer（Host-backed 优化器状态）

## Summary

当前 TorchTitan NPU 通过 `torchtitan_npu.override.common.optimizer.virtual` 将 Adam/AdamW 的 moments 创建为实际位于 Host、可由 NPU 算子访问的 swapped-memory 张量。它节省常驻 HBM，与显式 H2D/D2H 的 [NovaSwap](swap_optimizer.md) 具有不同生命周期，两个 override 都替换 `OptimizersContainer.Config`，不能同开。

## 当前配置

将下面入口追加到模型原有的 `override.imports`，保留已有 attention、RoPE、RMSNorm 等替换：

```text
--override.imports torchtitan_npu.override.common.optimizer.virtual
--checkpoint.enable
--checkpoint.async-mode disabled
```

不再设置 `optimizer.virtual_optimizer`、`virtual_optimizer_size`、`swap_optimizer_times`，也没有该容器的按 PP stage 容量列表。配置系统不会把旧字段自动转换成最新 override。

## 初始化与更新契约

容器给底层 Adam/AdamW 注册 step pre-hook，仅处理有梯度且 state 为空的参数，先创建普通 FP32 step scalar，再由 `_make_swap(p)` 分配 exp_avg/exp_avg_sq。DTensor 只取本 rank local shard 分配，再保留 mesh、placements、全局 shape/stride；本地空 shard 使用普通 empty_like，因为 swap allocator 不接受空张量。

最新代码还有 amsgrad 分支，将 max_exp_avg_sq 同样初始化为 swap-backed 张量；特性文档的“只包含两个 moments”描述未覆盖这一分支。这里只确认状态构造代码，不据此宣称 AMSGrad 已完成真机验证。

已有 state 不被 pre-hook 覆盖。当前代码没有旧 VirtualAllocator 的容量预算与任意异常回退机制；只有明确的 zero-sized shard 普通分配分支。不能把 allocation 失败当成会自动回退 HBM。

## Checkpoint 与已修复的 fresh-load 路径

`state_dict()` 会为尚无梯度、未初始化的参数补齐状态。`load_state_dict()` 先准备并保存 swap-backed destinations，再调用基础加载，把加载值 copy 到这些 destinations 并恢复引用。因此 fresh/existing/repeated load 都沿当前 destinations 逻辑，不再保留旧卡所述“首次 step 前加载会跳过 allocator”的缺陷结论。

extension `CheckpointManager` 对同步 native DCP 保存使用 `FileSystemWriter(per_thread_copy_ahead=0)`，避开 swap storage 与 copy-ahead 的不兼容；不需要额外 checkpoint override。可另启 `--checkpoint.extensions.verify-hash-manifest`。

该 writer 特化不覆盖 async、async-with-pinned-memory 或 HF 保存，它们继续委托上游。文档报告单 NPU 同步 save/load 与 load 后 step 验证，多卡、async/HF 尚未完成该特性的完整验证。本次仅复核源码，不能据此承诺拓扑、最低驱动版本或性能比例。

## MindSpeed 原生实现

torchtitan-npu 侧的 Virtual Optimizer 派生自 [mindspeed](../frameworks/mindspeed.md) 的 `virtual-optimizer` 特性，机制同源——都靠昇腾驱动的虚拟内存能力把 `exp_avg`/`exp_avg_sq` 的实际内存放在 Host、地址映射到 Device。差异在于 MindSpeed 跑在 Megatron-LM 栈上：动量是普通 FP32 张量（无 DTensor 包装），分配粒度与 checkpoint 适配走的是另一套代码。

### 特性开关与约束

`VirtualOptimizerFeature` 注册 CLI `--virtual-optimizer`，`nargs='+'` 收一串值，逐值经 `parse_list_for_virtual_optimizer`：`'all'` 解析为 `65.0`（源码注释「Maximum NPU memory」，单位 GB），否则 `float(value)`。三种用法：

- `--virtual-optimizer all` → 每个 PP stage 给 65 GB 预算（实质换出全部一二阶动量）；
- `--virtual-optimizer 2.0` → 每个 stage 统一 2 GB；
- `--virtual-optimizer 6 5 4 3` → 四个 stage 逐个 6/5/4/3 GB。

`validate_args` 两道校验：`torch_npu` 必须有 `empty_with_swapped_memory`，否则 `AssertionError` 提示升级 PTA；并 `incompatible_check(args, "fused_ema_adamw")`——**与 `fused_ema_adamw` 互斥**（排他对象与 torchtitan 侧「与 swap_optimizer 互斥」不同）。

### 按 PP stage 的字节预算分配

MindSpeed 的 `VirtualAllocator` 读取真实 PP rank/size，将配置换算为该 stage 的字节预算，按张量分配扣减；这不是当前 TorchTitan override 的无容量字段配置方式。`get_global_virtual_allocator` 惰性按 `(pp_rank, pp_world_size, args.virtual_optimizer)` 建一个全局 allocator 缓存到 `args` 上；`swap_size_this_pp_rank = get_swap_memory_size()[pp_rank] * 1024**3`（GB→字节）。`get_swap_memory_size` 的广播规则：长度为 1 → 广播到所有 stage；长度等于 `pp_stages` → 逐 stage；否则 `ValueError`；`None` → 全 0。

每个动量经 `create(p)` 分配，按预算余额二选一：

```python
def create(self, p):
    if self.swap_size_this_pp_rank > 0:
        return self.get_swap_memory(p)   # 虚拟内存：Host 常驻、Device 可寻址
    else:
        return self.get_npu_memory(p)    # 预算耗尽 → 退回 HBM zeros_like
# virtual_adam.py — VirtualAllocator.create
```

`get_swap_memory` 调 `torch_npu.empty_with_swapped_memory(p.size(), device=p.device)`，给 tensor 及其 `.data` 都打 `swap_tensor=True`、`zero_()` 后把本张量字节数从预算扣除、累加到 `actually_swap_size`（MB，按 rank 打印汇总）。一旦该 stage 预算用尽、或 `empty_with_swapped_memory` 缺失、或分配抛异常，都**回退到 `torch.zeros_like` 的 HBM 分配**——即预算决定换出多少动量，超出部分仍留显存。

### step 与更新算子

被 patch 的 `AdamW.step`（同时打 `mindspeed.optimizer.adamw` 与 `mindspeed.core.optimizer.adamw` 两处）走 `virtual_optimizer_step` → `virtual_optimizer_step_impl`：标准 AdamW 主循环，唯一改动是状态初始化处 `state['exp_avg'], state['exp_avg_sq'] = self.virtual_allocator.init_exp(p)`（虚拟还是 HBM 由预算决定）；amsgrad 的 `max_exp_avg_sq` 仍 `torch.zeros_like(p)` 常驻 HBM。更新调 `mindspeed.optimizer.adamw.adamw` 函数式接口，内部最终落到 `torch._fused_adamw_` 融合 kernel。不同容器的更新调用与状态生命周期分别核对。

### checkpoint 适配

虚拟内存张量没有随路计算单元、无法被直接拷贝/打印/保存，MindSpeed 用两层 patch 兜底：

- **全局张量方法 wrapper**：把 `torch.Tensor.{copy_, cpu, clone, npu, detach}` 换成 swap 感知版本。`swap_tensor_copy_wrapper` 对 swap 张量的同设备拷贝改用 `dst.fill_(1).mul_(src)`（乘法有计算通路）而非直接 `copy_`；`cpu`/`clone`/`npu` 经 `empty_like`+`copy_` 中转取出真值；`detach` 透传 `swap_tensor` 标记。
- **加载回链**：`replace_swap_tensor_wrapper` 包住 Megatron `DistributedOptimizer.load_parameter_state_from_dp_zero{,_legacy}` 与 `Float16OptimizerWithFloat16Params.load_state_dict`，在原加载完成后调 `virtual_optimizer_replace`，对每个 param 的 `exp_avg`/`exp_avg_sq` 做 `copy2swap`——重新申请虚拟内存并把加载值灌入，恢复「Host 真值、Device 可寻址」。

### 与多流 swap 的取舍

MindSpeed 文档给出虚拟内存相对手动多流 swap（即 [swap-optimizer](swap_optimizer.md) 那条路线）的取舍：虚拟内存省掉两次 UB↔HBM 搬运、直接由算子自身流水（MTE2/MTE3/Vector）做指令级并行掩盖，免去多流引入的流同步与额外显存开销；代价是 Host 虚拟内存**无随路计算**，涉及随路计算的算子用不了。文档推荐配 `CPU_AFFINITY_CONF=1,lazy_bind:0` 粗粒度绑核，把任务绑到 NPU 对应 NUMA 核、规避跨 NUMA 访问。当前文档已不再声明该组最低版本；按实际环境确认 swapped-memory 能力及特性校验。


## Evidence

- [virtual_optimizer.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/virtual_optimizer.md)（primary）
- [optimizer.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/optimizer.py)（implementation）
- [checkpoint.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py)（implementation）
- [virtual-optimizer.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/virtual-optimizer.md)（implementation）
- [virtual_adam.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/virtual_optimizer/virtual_adam.py)（implementation）
- [adaptor.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/optimizer/virtual_optimizer/adaptor.py)（implementation）
- [virtual_optimizer.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/features_manager/optimizer/virtual_optimizer.py)（implementation）

## Links

- [Swap Optimizer](swap_optimizer.md)
- [Muon](muon_optimizer.md)
- [DCP 与 HF 检查点](checkpoint_dcp_hf.md)
- [TorchTitan NPU](../frameworks/torchtitan.md)
