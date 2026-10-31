---
type: Concept
title: SuperKernel
description: SuperKernel 的 scope 调度与融合目标，当前 R1/LongCat 范围差异及通用编译选项和模型限制的边界。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:55:50Z'
platforms:
- a3
---

# SuperKernel

## Summary

TorchAir `ge_graph`（max-autotune）图模式下，**按用户声明的 scope 优化计算融合与任务调度** 的优化能力。目标是减少算子间任务调度的等待时间与下发开销，尤其针对 Decode 阶段大量细碎算子（MLA prolog、FA、MoE dispatch/combine、GroupedMatMul、finalize 等）叠加时的 host 下发与调度开销。

在 DeepSeek-R1 Decode W8A8C8 + MTP1 的 benchmark YAML (`decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml`) 中默认 `enable_superkernel: True`。

Scope 不保证其中全部算子融合为单个 kernel；固定 LongCat 来源明确部分算子尚不支持完全融合。

## Mechanism

通过 `executor.utils.superkernel_scope` 上下文管理器标记融合范围：

```python
from executor.utils import superkernel_scope

switch = enable_superkernel
scope = f"scope_name"
options = f"scope_options"
with superkernel_scope(switch, scope, options):
    ...  # 此处放入待融合模块；完整边界按固定模型核对
```

实际用例（当前 DeepSeek-R1 模型）：

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

- 本页scope helper使用TorchAir GE scope；当前通用npugraph_ex编译器另可传super_kernel_optimize选项，不能将该选项与GE scope混为同一API。模型可能额外拒绝组合（如LongCat拒绝npugraph_ex+SuperKernel），需分别检查。
- 源码显式条件 `enable_superkernel and not forward_metadata.is_prefill` → Prefill 路径不进入 SuperKernel scope。
- scope 边界不当会导致编译失败或性能退化。
- 与 micro-batch 的互动 source 未明确，待验证。

## Known Results

固定来源没有SuperKernel单项受控收益；完整组合结果见[R1 Decode 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_decode_source_benchmark.md)，不能归因给该融合开关。

## Evidence

- [deepseek_r1_decode_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（implementation）
- [common_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py)（implementation）
- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（constraint）

## LongCat-Flash 路径差异

LongCat-Flash 同样在 `ge_graph` 下使能 `enable_superkernel`。由于 LongCat-Flash 在不同流上采取了不同的分核策略（见 [moe-multi-stream](moe_multi_stream.md)），**按照分核、分流的范围标定各 SuperKernel scope 的范围**，即 scope 边界由控核边界驱动，而非 R1 那样按 decode layer 整体一个 scope。`modeling_longcat_flash.py` / `ffn.py` 中可见 `superkernel_scope` 多次出现。

> 当前 CANN 软件版本下，SuperKernel 标记范围内的部分 LongCat-Flash 算子尚不支持完全融合，将在后续社区版本中得到解决（LongCat-Flash README 说明）。

## Links

- [范围选择](../../optimizations/rules/superkernel_decode_ge_graph_fusion_scope.md)
- [LongCat范围](../../optimizations/cases/longcat_a3_superkernel_layout_fusion.md)
- [Qwen3-MoE范围](../../optimizations/cases/qwen3_moe_a3_superkernel_scopes.md)
- [当前图编译](../../guides/optimization/graph_mode_decode_only_compile_backends.md)
