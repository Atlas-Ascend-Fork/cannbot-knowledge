---
type: Optimization
title: weight-NZ 与 MC2 mm_all_reduce 融合按层互斥：走 MC2 的 RowParallel 层权重必须留 ND
description: weight-NZ 与 MC2 mm_all_reduce 融合按层互斥：走 MC2 的 RowParallel 层权重必须留 ND。在 TP prefill 里同时想开两个手段：① weight-NZ（把线性层权重转成昇腾 NZ / FRACTAL 内存格式提搬运效率）；② npu_mm_all_reduce_base（把 RowParallelLinear 的 Matmul 与 all_reduce 融成一步的 MC2 融合，减少中间搬运与通信调度）。两者对同一层的权重布局要求冲突——直接全开会撞。
tags:
- task.optimization
- topic.parallelism
- topic.data_movement.communication.collective_communication
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/402
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# weight-NZ 与 MC2 mm_all_reduce 融合按层互斥：走 MC2 的 RowParallel 层权重必须留 ND

## 适用场景

在 [TP](../../../concepts/parallelism/tensor_parallel.md) prefill 里同时想开两个手段：① [weight-NZ](../../../concepts/techniques/weight_nz.md)（把线性层权重转成昇腾 NZ / FRACTAL 内存格式提搬运效率）；② `npu_mm_all_reduce_base`（把 RowParallelLinear 的 Matmul 与 all_reduce 融成一步的 MC2 融合，减少中间搬运与通信调度）。两者对**同一层**的权重布局要求冲突——直接全开会撞。

## 条件 → 怎么门控

- **weight-NZ 要 NZ 权重、MC2 融合的 Matmul 路径要吃 ND 权重**：同一层不能既转 NZ 又走 MC2。
- **规则**：**凡走 MC2 融合的 RowParallelLinear 层，其权重必须留 ND、不转 NZ**；非 MC2 层照常按 `enable_weight_nz` 转 NZ。落地为按层门控 `is_nz`：

```python
use_mm_all_reduce_base = (
    enable_mm_all_reduce_base
    and isinstance(module, RowParallelLinear)
    and isinstance(quant_method, UnquantizedLinearMethod)
    and module.tp_size > 1 and module.input_is_parallel
    and module.bias is None and not module.skip_bias_add
    and name.endswith(mm_all_reduce_suffixes))       # o_proj / out_proj / down_proj 类输出投影
quant_method.process_weights_after_loading(
    module, is_nz=enable_weight_nz and not use_mm_all_reduce_base)   # ← MC2 层强制关 NZ
```

## MC2 融合本身的启用门控（一并对照）

`npu_mm_all_reduce_base` 使能需同时满足：**prefill 阶段** + 非量化路径（`UnquantizedLinearMethod`）+ TP 切分数 >1 且输入已按 TP 切分 + 无 bias 且不 `skip_bias_add` + 能取到 HCCL group name。不满足则回退常规 Matmul + `dist.all_reduce`。融合覆盖 full-attn `o_proj`、linear-attn `out_proj`、dense / shared-expert `down_proj` 这类 RowParallel 输出投影。

## 反例 / 边界

- 证据仅覆盖 cann-recipes-infer [Qwen3.5-MoE](../../../concepts/models/qwen3_5_moe.md) 建模里这几类 RowParallel 输出投影。
- 「MC2 要 ND」记作**本仓当前产出的布局门控 + commit 陈述意图**（commit 标题即「使能 mm allreduce 融合算子，并规避相关 weight 转 NZ 格式的操作」），**非算子规格文档确认**——不外推整个昇腾栈、不断言算子硬合约。融合算子按硬件 / shape 条件回退到非融合等价路径的更一般模式见 [fused-op-hardware-conditional-fallback](fused_op_hardware_conditional_fallback.md)；MC2 融合通信算子在别的平台 / 结构上的兼容边界（A2 专家上限、mm-reduce-scatter 未使能、fullmesh_v2 零专家）见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)。

## Evidence

- `diff 事实`（@843c3dd61a35）：`modeling_qwen3_5_moe.py` 的 `process_weights_after_loading`——`is_nz = enable_weight_nz and not use_mm_all_reduce_base`、`mm_all_reduce_suffixes` 列表、MC2 判定条件链；`qwen3_5_prefill_mm_all_reduce` 的回退逻辑与 `npu_mm_all_reduce_base(input_, weight.data, hcom, reduce_op="sum")`。
- `diff 行为 + commit 陈述意图`：「NZ 与 MC2 布局冲突、MC2 要 ND」＝ 代码强制关 NZ 的行为 + commit `078b23406e21` 标题「规避 weight 转 NZ」；非独立算子规格确认，按「converter 产出 ≠ 算子合约」措辞为「本仓当前这么门控」。
- 溯源下探：[cann-recipes-infer-pr-402-feat-support-qwen3-5](https://gitcode.com/cann/cann-recipes-infer/merge_requests/402)