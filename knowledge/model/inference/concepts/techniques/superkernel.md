---
type: Concept
title: SuperKernel
description: 'TorchAir `ge_graph`（max-autotune）图模式下，**按用户声明的 scope 将计算子图整体融合为单个大 kernel** 的优化能力。目标是减少算子间任务调度的等待时间与下发开销，尤其针对 Decode 阶段大量细碎算子（MLA prolog、FA、MoE dispatch/combine、GroupedMatMul、finalize 等）叠加时的 host 下发与调度开销。 在 DeepSeek-R1 Decode W8A8C8 + MTP1 的 benchmark YAML (`decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml`) 中默认 `enable_superkernel: True`。'
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# SuperKernel

## Summary

TorchAir `ge_graph`（max-autotune）图模式下，**按用户声明的 scope 将计算子图整体融合为单个大 kernel** 的优化能力。目标是减少算子间任务调度的等待时间与下发开销，尤其针对 Decode 阶段大量细碎算子（MLA prolog、FA、MoE dispatch/combine、GroupedMatMul、finalize 等）叠加时的 host 下发与调度开销。

在 DeepSeek-R1 Decode W8A8C8 + MTP1 的 benchmark YAML (`decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml`) 中默认 `enable_superkernel: True`。

## Mechanism

通过 `executor.utils.superkernel_scope` 上下文管理器标记融合范围：

```python
from executor.utils import superkernel_scope

switch = enable_superkernel
scope = f"scope_name"
options = f"scope_options"
with superkernel_scope(switch, scope, options):
 your modules
```

实际用例（`models/deepseek_r1/models/modeling_deepseek.py:L1605`）：

```python
with superkernel_scope(self.enable_superkernel and not forward_metadata.is_prefill,
 label, option):
 # 循环包裹全部 decode layers（单一 scope）的 attention + moe 流程
 ...
```

- `scope`：SuperKernel 的名称，决定融合范围的边界；
- `options`：SuperKernel 编译自定义选项；
- 支持将 **所有 decode layer 融合到一个 scope**，亦可按层/模块细分。具体边界调整由用户在 `modeling_deepseek.py` 中修改。
- R1 实参里 `label` 固定为 `decode_layer`，`option` 随 `self.enable_multi_streams` 切换——开多流时传 `stream-fusion=1` 以在 SuperKernel scope 内启用多流，否则为占位选项 `option_xxx2`。这是 SuperKernel 与 [moe-multi-stream](moe_multi_stream.md) 协同的关键接口语义。

详细使用请参考 [官方文档](https://www.hiascend.com/document/detail/zh/Pytorch/710/modthirdparty/torchairuseguide/torchair_00035.html)。

## Applicable Scenarios

- Decode 阶段（`forward_metadata.is_prefill == False`）。
- `exe_mode: "ge_graph"` 图模式。
- 目标是进一步压低 TPOT（host 下发 + kernel launch gap 成为瓶颈时）。

## Constraints

- **仅 ge_graph 模式支持**：`npugraph_ex`（reduce-overhead）与 eager 模式下不可用。
- 源码显式条件 `enable_superkernel and not forward_metadata.is_prefill` → Prefill 路径不进入 SuperKernel scope。
- scope 边界不当会导致编译失败或性能退化。
- 与 micro-batch 的互动 source 未明确，待验证。

## Known Results

README 与 decode 优化文档未给出 SuperKernel 单项提升数据。在叠加 W8A8C8 + MTP1 + perfect eplb 的完整 benchmark 下，Decode TPOT 44.9 ms / 2138 tokens/p/s（见 [deepseek-r1](../models/deepseek_r1.md)）。**SuperKernel 单项收益数据缺失，待验证**。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_decode_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md) "SuperKernel 优化"章节
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek_r1/config/`](https://gitcode.com/cann/cann-recipes-infer/tree/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/config)（`decode_r1_rank_128_128ep_a8w8c8_mtp*.yaml` 中 `enable_superkernel: True`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek_r1/models/modeling_deepseek.py#L1605`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/models/modeling_deepseek.py#L1605)（`superkernel_scope` 使用处）

## LongCat-Flash 路径差异

LongCat-Flash 同样在 `ge_graph` 下使能 `enable_superkernel`。由于 LongCat-Flash 在不同流上采取了不同的分核策略（见 [moe-multi-stream](moe_multi_stream.md)），**按照分核、分流的范围标定各 SuperKernel scope 的范围**，即 scope 边界由控核边界驱动，而非 R1 那样按 decode layer 整体一个 scope。`modeling_longcat_flash.py` / `ffn.py` 中可见 `superkernel_scope` 多次出现。

> 当前 CANN 软件版本下，SuperKernel 标记范围内的部分 LongCat-Flash 算子尚不支持完全融合，将在后续社区版本中得到解决（LongCat-Flash README 说明）。

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [kimi-k2-thinking](../models/kimi_k2_thinking.md)
- [longcat-flash](../models/longcat_flash.md)
- [hy3-preview](../models/hy3_preview.md)（Decode 层循环外包单个 `superkernel_scope`；combine_v2 `shared_expert_x` 融合因 >2 stream 限制回退）
- [moe-multi-stream](moe_multi_stream.md)
- [moe-dispatch-combine-v2](moe_dispatch_combine_v2.md)（combine_v2 `shared_expert_x` 在 CANN 8.5.0 与 >2 real stream SuperKernel 不兼容，hy3-preview 已回退）
- [torchair](../frameworks/torchair.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [deepseek-v4](../models/deepseek_v4.md)（Future Plan：使能 Super Kernel 降低算子启动/调度间隙）
- [multi-stream](multi_stream.md)（图模式多流 `stream-fusion=1` scope 与多流编排协同）