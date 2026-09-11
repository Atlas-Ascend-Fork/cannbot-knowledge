---
type: Concept
title: NPU 图模式（ge_graph / npugraph_ex）
description: Pytorch 默认 `eager` 模式"边解释边执行"，逐算子下发 Device，推理场景容易暴露 Host 侧下发开销（**host bound**）。图模式通过 `torch.compile` 把前向逻辑捕获成图、交给 NPU 后端编译执行，**减少 Host 下发开销，允许后端在更大范围做融合、内存复用、调度优化**，显著降低 decode 时延。 NPU 图模式有两种实现路径：**GE 图模式**（FX → Ascend IR → GE 引擎编译）与 **npugraph_ex**（基于 npugraph capture & replay，强调下沉调度与低开销执行）。历史代码里的 `acl_graph` 命名对应当前 `npugraph_ex`，**将逐步废弃**。 cann-recipes-infer 通过 cann-executor 的 `model_config.exe_mode` 配置开关，图模式开关**仅对 decode 生效**，prefill 统一走 eager——prefill shape/控制流动态变化，容易断图或重编译，且单次算子执行更长、下发 bound 不突出。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/cann/npu_graph_optimization.md
  role: supporting
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- agnostic
---

# NPU 图模式（ge_graph / npugraph_ex）

## Summary

Pytorch 默认 `eager` 模式"边解释边执行"，逐算子下发 Device，推理场景容易暴露 Host 侧下发开销（**host bound**）。图模式通过 `torch.compile` 把前向逻辑捕获成图、交给 NPU 后端编译执行，**减少 Host 下发开销，允许后端在更大范围做融合、内存复用、调度优化**，显著降低 decode 时延。

NPU 图模式有两种实现路径：**GE 图模式**（FX → Ascend IR → GE 引擎编译）与 **npugraph_ex**（基于 npugraph capture & replay，强调下沉调度与低开销执行）。历史代码里的 `acl_graph` 命名对应当前 `npugraph_ex`，**将逐步废弃**。

cann-recipes-infer 通过 [cann-executor](../frameworks/cann_executor.md) 的 `model_config.exe_mode` 配置开关，图模式开关**仅对 decode 生效**，prefill 统一走 eager——prefill shape/控制流动态变化，容易断图或重编译，且单次算子执行更长、下发 bound 不突出。

## Mechanism

### GE 图模式 vs npugraph_ex 对比

| 维度 | `ge_graph` | `npugraph_ex` |
|------|-----------|---------------|
| 实现路径 | FX → Ascend IR → GE 引擎编译执行 | npugraph capture & replay，下沉调度 |
| 配置承载 | `CompilerConfig.experimental_config` 成员 | `options` kwargs |
| 普通编译后端 | `backend = tng.get_npu_backend(...)` | `backend = "npugraph_ex"` |
| 缓存编译接口 | `tng.inference.cache_compile(...)` | `torch.npu.npugraph_ex.inference.cache_compile(...)` |
| `dynamic` 默认 | `False` | `True` |
| 专属配置项 | `frozen_parameter` / `tiling_schedule_optimize` / `topology_sorting_strategy` | `static_kernel_compile` / `frozen_parameter` |
| 特性支持 | 支持 [superkernel](superkernel.md) | 支持 `enable_static_kernel` |
| 推荐场景 | 功能稳定、性能更优，当前默认首选 | 使用体验接近 eager，后续主推；算子接口补齐 Tensor 输入后会调整 `dynamic` |

> **为何 `npugraph_ex` 当前保持 `dynamic=True`**：并非图本身必须动态，而是**配套的 FIA 算子接口**里 `actual_seq_lengths` 等入参暂不支持 Tensor 输入，只支持 `list[int]`。若强行 `dynamic=False`，容易触发重编译。后续算子接口补齐 Tensor 输入支持，这里配置也会调整。

### 使能链路

```
1. 配置层：executor/core/config/inference_config.py
 model_config.exe_mode ∈ {eager, ge_graph, npugraph_ex}

2. 预热层：executor/core/engine/execution_engine.py::warm_up
 先跑一次 prefill（eager） → 再跑一次 decode（触发图编译）

3. 编译层：executor/core/model_worker/model_worker.py::compile_model
 → executor/utils/graph_utils.py::compile_model_forward

4. 执行层：ModelWorker.inference
 if not is_prefill and exe_mode in ["ge_graph", "npugraph_ex"]:
 return self.model_compiled(**model_inputs)
 else:
 return self.model(**model_inputs)

5. 元数据层：executor/utils/forward_metadata.py::ForwardMetaData
 is_prefill / kv_len / actual_seq_lengths_q / actual_seq_lengths_kv / attention_mask
 由框架构造后作为显式输入传入模型
```

### 通用准备逻辑

```python
# 来源：executor/utils/graph_utils.py
import torchair as tng
import torchair.ge_concrete_graph.ge_converter.experimental.patch_for_hcom_allreduce

tng.patch_for_hcom() # 处理集合通信入图；PyTorch 2.6+ 通常可省略
torch._dynamo.config.inline_inbuilt_nn_modules = False # 避免内建模块被过度内联
```

### 编译缓存（cache compile）

- **解决问题**：重复启动或重复执行同一图时的启动开销。
- **命中前提**：模型结构、输入 shape、dtype、图模式配置均保持稳定；缓存目录一致。
- **接口差异**：`ge_graph` → `tng.inference.cache_compile`；`npugraph_ex` → `torch.npu.npugraph_ex.inference.cache_compile`。

## 模型适配五条件

仅仅开 `exe_mode` 不够，模型本身必须满足：

1. **eager 下稳定运行** —— 图模式不会修复 eager 下本来就存在的错误。
2. **prefill 与 decode 明确区分** —— 推荐 `prefill` 保持 eager、`decode` 使用图模式；用 `forward_metadata.is_prefill` 或独立的 `prefill/decode` 方法区分路径。
3. **动态信息显式输入** —— `kv_len`、`position_ids`、`actual_seq_lengths_q/kv`、`is_prefill` 由框架构造传入，而非模型内部临时生成 Python 标量或隐式推导。
4. **KV Cache 与常驻 buffer 预分配 + 原地更新**：

 ```python
 # 错误：decode 场景下 KV 的 shape/地址变化 → dynamo guard 失败 + 重编译
 key = torch.cat([past_key, new_key], dim=1)

 # 推荐：原地更新
 torch_npu.scatter_update_(k_cache, kv_len, key_states, -2)
 torch_npu.scatter_update_(v_cache, kv_len, value_states, -2)
 ```

5. **避免典型 Graph Break 写法**：
 - `tensor.item`
 - 基于 Tensor 值的 Python `if/while`
 - 在 forward 内部临时创建影响 shape 的控制分支
 - 根据 Python `list/tuple` 长度变化切换图内控制流

## FIA 融合算子适配建议

| 模式 | 常见 FIA 接口 | `actual_seq_lengths` | 说明 |
|------|--------------|----------------------|------|
| `ge_graph` | `torchair.ops` | Tensor | 只适合 GE 图模式 |
| `npugraph_ex` | `torch_npu` | `list[int]`（推理常见） | 当前 FIA 接口主打推理；算子支持变化时再调整 |

参考 `models/qwen3_moe/models/modeling_qwen3_moe.py`：decode 且 `enable_gegraph` 时切到 `torchair.ops`；ExecutionEngine 在 `npugraph_ex` decode 模式下把 `actual_seq_lengths_*` 转成 `list`。

### FIA layout × 图后端 兼容性（经验）

下表汇总已在真实模型上验证过的 layout × FIA 接口 × 图后端 × `actual_seq_lengths` 组合。**不要跨组合直接迁移**：即使是同一模型同一算子，换其中一个参数就可能引入 aicore crash 或精度漂移。

| layout | FIA 接口 | 图后端 | `actual_seq_lengths_kv` | `dynamic` | 已验证案例 | 备注 |
|--------|----------|--------|-------------------------|-----------|------------|------|
| BSH | `torch.ops.npu.*` | `ge_graph` | `list[int]` | `True` | PASS | 仓内 qwen3-moe 参考路径；成熟稳定 |
| BNSD | `torch.ops.npu.*` | `ge_graph` | `list[int]` | `True` | **FAIL**：首次 replay aicore `EZ9999 MTE DDR out of range / 507011`；`mark_static(q/k/v)` 无效 | **不可用**组合 |
| BNSD | `torchair.ops.*` | `ge_graph` | Tensor | `False` | **FAIL**：精度 3/16 漂移 + 单步 1970 ms；假设根因是 torchair GE 在 `dynamic=False` 下对 72 个 `register_buffer` in-place 更新的别名跟踪不完整 | **精度风险高**，慎用 |
| BNSD | `torch.ops.npu.*` | `npugraph_ex` | `list[int]` | `True` | PASS | 已验证的备选路径 |
| BSH | `torch.ops.npu.*` | `npugraph_ex` | `list[int]` | `True` | PASS | 需配合下文"npugraph_ex options 推荐"使用 |

**组合边界**：BSH+GE、BNSD+npugraph_ex、BSH+npugraph_ex 三种 layout×后端组合在同一受测模型上均验证成立，精度全部 16/16 bit-exact；不能仅凭 BSH 或 BNSD 布局限定图后端。

**性能比较边界**：所记录的 decode 稳态（14.43 / 13.77 / 11.20 ms）**差异主要不来自 layout×后端组合本身**，而来自每轮叠加的算子/模式优化是否相同。将 "decode 数字" 与 "layout×后端" 绑定会造成选型误导。以 11.20 ms 配置相对 13.77 ms 配置的 -2.57 ms/step 为例，其中 ~80% 归因于**与 layout/后端正交的三项专属优化**：
1. `npu_interleave_rope` 取代 `npu_rotary_mul`（partial RoPE D=64 直绑定）
2. GDN `recurrent_state` 彻底 op-native 布局预分配（`(B, N_v, D_v, D_k)` 零 transpose）
3. 懒 buffer 图外 materialize（`register_buffer(persistent=False)` + `_force_materialize*` + `model.apply(...)`）

这三项原则上可移植到 BSH+GE 或 BNSD+npugraph_ex 路径（具体兼容性需独立 A/B 验证，参考上文"FIA layout × 图后端 兼容性"表的逐组合结论）。因此选型建议是：

- **路径（layout×后端）选择**：按**可行性**决策——GE 不可用时切 npugraph_ex；BSH 与 BNSD 按现有实现和已验证的兼容性选择
- **正交优化**：无论走哪条路径，都应评估 `npu_interleave_rope`（若 partial RoPE）、op-native cache 布局（若 SSM/GDN 族）、懒 buffer 图外 materialize 三项是否适用；这些是真正影响 decode 稳态的差别项

如果当前组合执行失败，可先评估更换图后端，再评估调整 layout；上述正交优化可分别验证后保留。

### npugraph_ex options 推荐模板（经验性，适用含 in-place 更新与懒 buffer 的模型）

下述 `torch.compile` options 组合用于处理含大量 `register_buffer` 原地更新和懒分配 buffer 的模型，可作为 Hybrid-Attention / Mamba 族 / GatedDeltaNet 模型的调试起点；适用性仍需按具体模型验证。

```python
torch._dynamo.config.recompile_limit = 64

model.decode_forward = torch.compile(
 model.decode_forward,
 backend="npugraph_ex",
 dynamic=True,
 fullgraph=False, # 或 True，取决于是否已消尽 graph break
 options={
 "inplace_pass": False, # 关掉 dynamo 对 inplace 的重写 pass
 "input_inplace_pass": False, # 同上（input 级）
 "clone_output": True, # 每个子图 output 克隆，打破跨 aclgraph live tensor 依赖
 "capture_limit": 256, # aclgraph 容纳上限；24 层独立 aclgraph 需要
 },
)
```

作用说明：

- `inplace_pass=False` + `input_inplace_pass=False`：规避 dynamo 对 `a.mul_(b)` 等 inplace 算子做 shape 合法性重写时的假阳性（典型症状 `aclnnInplaceMul selfRef [1,1,16] vs [16]`），代价是潜在失去 inplace 的内存复用优化
- `clone_output=True` + `capture_limit=256`：为每个子图 output 克隆，避免"前一 aclgraph 仍持有的 output tensor 被后一 aclgraph 的 pool state 回滚"引发的 `definitely_stale_pointers` 断言
- **代价**：首步 aclgraph capture 编译时间会放大（所记录配置从典型 41 s 放大到 88 s，约 2×）；适合长输出 / 服务端热启动场景，不适合对冷启动延迟敏感的单次推理

### 懒 buffer 必须图外 materialize（前置 checklist）

任何形如 `if need_rebuild: self._cache = <compute_from_weights>` 的懒初始化在 NPU 首次 forward 时 trigger，会被 dynamo trace 成独立小 aclgraph 片段。多层模块重复此模式 → capture_limit 内 aclgraph 交叉引用 output tensor → 下一 capture 回滚 pool state 时命中 `definitely_stale_pointers`。

**标准模式**（推广到任何 lazy 合成 tensor：gamma=1+w 预 cast、合并权重、QKV 合并等）：

```python
class MyModule(nn.Module):
 def __init__(self, ...):
 super().__init__()
 # 非持久 buffer：from_pretrained 时不要求 state_dict 里有同名 key，但受 device_map 搬运影响
 self.register_buffer("_my_cache", torch.empty(...), persistent=False)

 @staticmethod
 def _force_materialize(module):
 """供 model.apply(...) 调用；必须在图编译前跑一次"""
 if isinstance(module, MyModule):
 with torch.no_grad():
 module._my_cache.copy_(<compute_from_weights>)

 def forward(self, x):
 # 不要在这里写 if not self._materialized: ... 分支
 return f(x, self._my_cache)

# Runner 侧
model.to(device) # device_map / from_pretrained
model.apply(MyModule._force_materialize) # 图外一次性物化
model = torch.compile(model, backend="npugraph_ex", ...)
```

**注意**：`register_buffer(persistent=False)` 在 `from_pretrained(device_map=...)` 搬运过程中可能被替换成 empty-on-device（未初始化内存，对应下文 Troubleshooting 表"初值被丢弃"行）。两种修法：
1. **本案例模式**：用 `_force_materialize_*` 静态方法 + `model.apply(...)` 在 `to(device)` 之后再物化（顺序保证）
2. **或**：在 `_init_weights` / `_post_init` 中显式 `nn.init.ones_(buf) / nn.init.zeros_(buf)` 补回初值

## 模型接入推荐顺序

按顺序推进，不要一次性把所有优化叠上去：

1. **跑通 eager 并确认精度正确**。
2. **消除 graph break 与重编译风险** —— 去掉 `.item` / 动态 Python 控制流，固定 KV cache 与常驻 buffer 地址/shape，明确 `actual_seq_lengths` 的类型来源。
3. **功能精度验证** —— 对比 eager 和 graph 输出，覆盖一轮 prefill + 多轮 decode；MTP 模型还需确认主模型与 MTP 模型的图模式输入 shape/dtype/长度组织稳定。
4. **按需开启增强特性** —— `enable_cache_compile` / `enable_static_kernel`（仅 `npugraph_ex`） / 模型自带 `enable_superkernel`（目前仅 `ge_graph`） / 多流 / 限核。

## Troubleshooting 速查表

| 现象 | 常见根因 | 处理建议 |
|------|----------|----------|
| 编译前就报错 | eager 路径本身不正确，或输入 shape/dtype/长度组织不稳定 | 先单独验证 eager，再检查图模式输入和前向参数组织 |
| 图捕获中断（Graph Break） | `.item` / Tensor 驱动的 Python 分支 / print / 自定义算子未适配 | 改写为 Tensor 逻辑，或补齐入图适配 |
| decode 性能没提升甚至变差 | 发生重编译；`kv_len`、`actual_seq_lengths_*`、缓存地址或输入 shape 不稳定 | `torch._logging.set_logs(recompiles=True)` 检查重编译原因，重点看 guard 变化来源 |
| `actual_seq_lengths` 类型报错 | 图模式与 FA 接口不匹配 | `ge_graph` 优先 Tensor + `torchair.ops`；`npugraph_ex` 对齐仓内当前 `list[int]` 方案 |
| `enable_static_kernel` 报错 | 模式不对 | 该选项仅允许在 `npugraph_ex` 模式使用 |
| SuperKernel 相关报错 | 在不支持的模式上开启 | 目前仅 `ge_graph` 支持 |
| 通信无法入图 | 依赖版本的集合通信入图前置处理未完成 | 根据当前 PyTorch / TorchAir 版本检查是否需要 `torchair.patch_for_hcom()` 等前置 |
| cache compile 不生效 | 缓存目录、输入 shape/dtype/长度组织或配置变化 | 固定 cache 目录，避免模型代码或编译参数频繁变化 |
| 图模式下精度异常 | KV cache / FA / 原地更新语义变化 | 先回退 eager 对齐，再逐项恢复优化 |
| torchair GE 首次 replay 即 `EZ9999 aivec 0x800000 / MTE DDR out of range / 507011` | 实测 BNSD layout + `torch.ops.npu.npu_fused_infer_attention_score` + `list[int]` 组合不可用；独立最小复现仍失败 | 可尝试切到 `npugraph_ex` + `torch.ops.npu.*` + `list[int]` + `dynamic=True`（参考上文"FIA layout × 图后端 兼容性"表的 BNSD/npugraph_ex 组合）。若必须保留 GE，考虑把 layout 改成 BSH |
| torchair GE 进图成功但 decode 精度前 N 对齐、第 N+1 起漂移 | `dynamic=False` 下对模型内大量 `register_buffer` 的 in-place 更新别名跟踪不完整（假设根因） | 切 `npugraph_ex`（CUDA-graph 语义下原地更新是一等公民）；若暂无条件切换，把可疑 buffer 改为图外管理的入参 tensor 再验证 |
| `npugraph_ex` 判定为"未安装" | import 路径错误（裸写 `import npugraph_ex`） | 正确导入是 `from torch_npu.npu import npugraph_ex`；`torch.compile(backend="npugraph_ex", ...)` |
| aclgraph capture 中 conv 报错 | 默认内部 format 与 aclgraph 不兼容 | `torch.npu.config.allow_internal_format = False` |
| aclgraph capture 中 inplace-mul shape 校验挂 | `A * B` 对 `.mul_` 的 broadcast 校验严格 | 在 forward 外或 lazy init 中显式 `.view(...)` 对齐 shape（如 `A_log / dt_bias` reshape 到 `[1, 1, 16]`） |
| `register_buffer(persistent=False)` + `from_pretrained(device_map=...)` 初值被丢弃 | torch 在 `device_map` 搬运时覆盖 buffer 为 empty-on-device | 方案一：`_init_weights` 显式 `nn.init.ones_/zeros_` 补回。方案二：提供 `_force_materialize_*` 静态方法 + Runner 在 `to(device)` 后 `model.apply(...)` 物化 |
| npugraph_ex 下运行首层或 q_norm 就报 `Expected allocated_pointer != definitely_stale_pointers.end` | 模型存在懒构建 buffer（典型 `Qwen3_5RMSNorm._gamma_plus_one` 的 `if need_rebuild:` 分支 / `_get_gate_up_weight` 的 lazy merge）。dynamo 把每层的懒分支 trace 成独立 aclgraph 片段，capture_limit 内多个子图交叉持有 output tensor，下一 capture 回滚 pool state 时命中 stale pointer 断言 | 参考上文"懒 buffer 必须图外 materialize"章节：懒初始化改 `register_buffer(persistent=False)` + `_force_materialize_*` 静态方法，Runner 在 `to(device)` 之后 `model.apply(...)` 物化 |
| npugraph_ex 下多层 aclgraph 交叉引用 live output tensor，`definitely_stale_pointers` 断言 | 默认 options 下每个子图 output 可能与下一子图 input 共享地址 | `options={"clone_output": True, "capture_limit": 256}`：为每个子图 output 克隆，并放宽 aclgraph pool 上限；代价是首步编译时间放大（典型 ~2×） |
| `aclnnInplaceMul selfRef [1,1,16] vs [16]` 或类似 inplace 算子 shape 不匹配 | dynamo 的 `inplace_pass` 把 `A * B` 优化成 inplace 写，广播 shape 被严格校验失败（典型 GDN 中 `A_log * a + dt_bias` 的 1D Parameter） | 方案一：`options={"inplace_pass": False, "input_inplace_pass": False}` 关掉 inplace 重写 pass。方案二：在 forward 外或 lazy init 中显式 `.view(1, 1, -1)` 对齐 shape |

## Constraints

- **图模式只对 decode 生效**（cann-recipes-infer 执行器约定）。
- **`ge_graph` + SuperKernel 可组合**（如 DeepSeek-R1 `decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml`）；**`npugraph_ex` 不支持 SuperKernel**。
- **MTP 与图模式的兼容性按模型而异**：DeepSeek-R1 `ge_graph + MTP1` 可共存；Qwen3-Next 的 MTP 与 SGLang ACLGraph 互斥。见 [mtp-speculative-decoding](mtp_speculative_decoding.md)。
- **`enable_static_kernel` 仅 `npugraph_ex` 可用**。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/cann/npu_graph_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/cann/npu_graph_optimization.md)（全文 270 行，涵盖原理、两种模式对比、使能链路、五条件、FIA 建议、Troubleshooting）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/utils/graph_utils.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/utils/graph_utils.py)（`compile_model_forward`）、[`executor/core/model_worker/model_worker.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/model_worker/model_worker.py)（`compile_model`）、[`executor/core/engine/execution_engine.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/engine/execution_engine.py)（`warm_up`）
- 官方资料：[TorchAir 文档总览](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh)、[GE / Ascend IR](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh/ascend_ir/ascend_ir.md)、[npugraph_ex 后端](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh/npugraph_ex/npugraph_ex.md)

## Links

- [torchair](../frameworks/torchair.md)
- [cann-executor](../frameworks/cann_executor.md)
- [inference-config](inference_config.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [qwen-dense](../models/qwen_dense.md)（覆写 `ModelRunner.graph_compile`；`ge_graph` + `npugraph_ex` 均已验证）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（Decode 整图、Prefill eager；`ge_graph` 默认 / `npugraph_ex` 备选，A3 上 ge_graph 稳态更优、npugraph_ex 编译更快）
- [hy3-preview](../models/hy3_preview.md)（`ge_graph` Decode 整图、Prefill eager；MC2 dispatch/combine 替代手动 all_to_all 消除 graph break）
- [superkernel](superkernel.md)
- [mtp-speculative-decoding](mtp_speculative_decoding.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [aicpu-scheduler](aicpu_scheduler.md)（值依赖分核下沉 AICPU，aclgraph 友好、metadata 单次复用）
- [autofuse](../frameworks/autofuse.md)（`torch.compile` 下游的 Inductor NPU 自动融合 Codegen 后端；图捕获/执行在前，AutoFuse 做 vector 子图融合编译）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（LongCat-Flash 减配验证模型，`ge_graph` 后端 Decode 整图（`fullgraph=True`）、Prefill eager；NgramEmbedding 整体入图、MoE identity expert 用乘法掩码绕过 GE 不支持布尔索引）
- [sam-speculative](../../../training/concepts/techniques/sam_speculative.md)（跨域·训练：Qwen3 RL 中 npugraph_ex 与 SAM 叠加 +29~33%）
- [qwen3-rl](../../../training/guides/recipes/qwen3_rl.md)（跨域·训练：Qwen3 RL 使能 npugraph_ex 图模式）
- [hunyuan3d](../../../spatial/concepts/models/hunyuan3d.md)（跨域·空间智能：Hunyuan3D shapegen 图模式适配）
- [multi-stream](multi_stream.md)（多流编排在 ge_graph / npugraph_ex 图模式下落地，切流/同步/控核接口随执行路径不同）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[pi0](../../../embodied/concepts/manipulation/pi0.md)、[isaac-gr00t](../../../embodied/concepts/manipulation/isaac_gr00t.md)、[pi05](../../../embodied/concepts/manipulation/pi05.md)、[om-atc-offline](../../../embodied/concepts/techniques/om_atc_offline.md)、[flow-matching-action-expert](../../../embodied/concepts/modules/flow_matching_action_expert.md)（VLA 在线推理 / OM 离线用图模式）

## Notes

- **ambiguity**：旧代码/文档里 `acl_graph` 命名仍存在，但**当前应对应 `npugraph_ex`**；新接入模型按 `ge_graph` / `npugraph_ex` 配置。