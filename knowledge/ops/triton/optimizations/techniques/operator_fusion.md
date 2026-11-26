---
type: Optimization
title: 算子融合策略
description: Triton Ascend 算子融合决策框架：融合收益分析、Cube/Vector 并行融合模式与 constexpr 条件编译门控。
tags: [task.optimization, topic.compute.composite, topic.implementation.pipeline, topic.programming_model.execution_unit.cube, topic.programming_model.execution_unit.vector, topic.compilation]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/index.md
  role: supporting
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-09-08T09:05:00Z'
platforms: [a2, a3]
---
# 算子融合策略

融合消除连续算子间的中间 HBM 读写。对内存密集型算子（elementwise, normalization），HBM 往返是主要成本。融合将数据保留在 UB（192KB, 片上, 零 HBM 开销）。

## 融合收益分析

分离执行：GEMM (load A,B→compute→store C) + RMSNorm (load C→compute→store Y) = 3 次 HBM 操作

融合执行：GEMM (load A,B→compute C)→**C 留 UB**→RMSNorm→store Y = 1 次 HBM 操作（消除 66% HBM 流量）

## OPT-triton-fusion-001: 融合决策

满足以下条件时融合：
- 连续算子间无跨 tile 数据依赖
- 中间 tensor 尺寸 ≤ UB 容量
- 后序算子为 element-wise（非 Softmax/归约）

## OPT-triton-fusion-002: constexpr 条件门控

```python
@triton.jit
def fused_kernel(..., HAS_BIAS: tl.constexpr, HAS_RESIDUAL: tl.constexpr):
    # 编译期分支消除：不影响无此 feature 的代码路径
```

## 实测：multi-kernel 与 full single launch 的 fusion tax

同一代表性 GEMM-heavy 算子、同一多 kernel 基线：

| 交付形态 | 相对基线 |
|---|---|
| multi-kernel + stage-level fused epilogue | ≈1.36× |
| full single launch | ≈0.74×（比 fused epilogue 慢约 1.8×） |
| 与多 kernel 同阶段结构的单 kernel 版 | 慢约 15.4% |

- 强制 full single launch 时所有 phase 共用一套 `multibuffer_mode` / tile：大 tile 的 fp32 累加器要固定 `l0c`，producer 流水深度被动降级，这就是 tax 的来源。
- 融合收益的顺序是：先消掉中间量 GM 往返（fused epilogue），再谈单 launch；把两者混在一起调，会把"省下的搬运"和"流水降级"互相掩盖。
- 交付判定与 [多输出 GEMM 链的融合与单 launch 化](multi_output_gemm_chain_fusion.md) 的三分支表一致：
  单 launch 仅是优化目标时按收益取舍；单 launch 为硬约束、性能仅观测时交付满足精度与 launch 的版本并单列性能；
  两者同时是硬约束时任一未满足即验收未通过。融合尝试后仍无符合精度与 launch 契约（或性能硬门槛）的候选时，
  才采用多 kernel 回退并记录 `contract_conflict`；**该回退只是"待确认的替代方案"，验收状态仍为未通过**（`target_reached=false`、
  交付形态不满足 launch 硬约束），报告中不得表述为已满足验收。

单 launch 的可行性门、交接形态谱与失败归因见 [单 kernel 单 launch 的可行性体系](single_kernel_feasibility.md)。

## OPT-triton-fusion-003: Cube/Vector 并行

```python
with dl.async_task(0):   # Cube
    acc = tl.dot(a, b)
with dl.async_task(1):   # Vector
    out = activation(acc)
```

