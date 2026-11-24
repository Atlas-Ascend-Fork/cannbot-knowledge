---
type: Optimization
title: bf16 受限 T2-ES1 整行向量排序 self-select
description: 把 useVectorSortT2_ self-select 门控收窄为仅 bf16 整行 Sort 几何，fp16 等明确留在标量堆。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-t2-bf16-vecsort-selfselect.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "gate 必须同时约束 dtype（bf16-only）与 geometry（整行/chunkCount==1）",
      "任何放宽 dtype 的尝试都必须先对目标 case 官方路径 spot_check"
    ],
    "excluded_conditions": [
      "fp16/half 及 radix key——实证在 sortLen=511 k=100 下向量路径 ~2x 回归",
      "sortLen>256 的其他 dtype（沿用 topk-t2-gather-vector-select 的 sortLen<=256 排除）",
      "多 chunk（chunkCount>1）大轴——走 chunked-vector-sort-merge"
    ],
    "required_conditions": [
      "T2 Q>1 ES1（chunkCount==1 整行）、dtype==bfloat16_t",
      "sortLen 在 [128,4096] 且整行向量 Sort 的 UB/LCM 预算可容纳",
      "非 radix key（bf16）整行 AscendC::Sort 路径存在且已验证"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "ee369507c943ea992aca99112dffa37e9f736cb6b678e48851f6a572f3816ecb",
      "decision_sha256": "1820aa26dc032c35384da9b31cd333f5cef7c08855c9ef9041b3e86c7b6037d9",
      "operator_class": "sort-select",
      "performance_sha256": "e4399e0bb5051cefbb43edbbd3316c88b73e96ca5a4cb39dc52a3c667d664fb2",
      "round": 5,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "070d72687942f4bb201cb16f142c5489aa8ffe90fe6d70f3172b5a82c1cf0ab4",
      "verify_sha256": "ad8f7e6a5a67930f6e942fb8f41c81590aaf611aad58dcb7998214cfeee069f3"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bounded-heap-when-vector-path-latent",
      "t2-scalar-heap"
    ],
    "dtypes": [
      "bf16"
    ],
    "pattern": "bf16-restricted-t2-es1-vecsort-selfselect",
    "reduce_mode": "top-k",
    "structure": [
      "t2-q1-es1-whole-row",
      "gather-compact-slots-vf",
      "whole-row-ascendc-sort"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-T2-BF16-VECSORT-SELFSELECT",
  "implementation_steps": [
    "确认 case_18 运行时 geometry（T2 Q>1 ES1、bf16、sortLen=255）",
    "在 Init 添加 bf16-only useVectorSortT2_ self-select（放在缓冲分配前）",
    "fp16 等其他 dtype 保持标量堆（round-4 教训）",
    "verify 全量 + case_18/case_20 官方路径 spot_check"
  ],
  "intent": "为 case_18（bf16 [255,8193] k=128 dim=0 largest=false，baseline 官方 12290us 标量堆）激活已验证的向量整行 Sort 路径，同时规避 round-4 的 fp16 回归（case_20 必须保持标量堆）。",
  "mechanism": "Init 中解码运行时字段后设 useVectorSortT2_=1，门控 ROUTE==2 && axisBlockLen_>1 && chunkCount_==1 && T==bfloat16_t && sortLen∈[128,4096] 且整行 Sort UB 可驻留；fp16/half 显式排除（round-4 实证 2x 回归）；不匹配逐字节回退标量堆。",
  "name": "bf16 受限 T2-ES1 整行向量排序 self-select",
  "operator_class": "sort-select",
  "operator_scope": "TopK T2 Q>1 ES1（chunkCount==1 整行）且 dtype==bfloat16_t 的 case：非 radix key 走整行 AscendC::Sort 路径，官方路径收益可复现（case_18 sortLen=255 k=128）。",
  "principle": "同一向量代码路径对不同 dtype/geometry 收益方向不同：bf16 走整行 AscendC::Sort（非 radix）在 sortLen<=256 的整行几何下净收益巨大（14x），而 fp16 走 RADIX_SELECT 在同区间回归 2x。把 self-select gate 收窄到经验证的单 dtype 几何，可同时拿到收益与避开回归。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize"
  ],
  "risks": [
    "放宽 dtype 集合会重新引入 round-4 的 fp16 回归",
    "bf16 整行 Sort 的 UB/LCM 预算在不同 sortLen 下需复核",
    "依赖宿主 tiling 字段不生效的前提（后续 host 修复会改变条件）"
  ],
  "slug": "topk-t2-bf16-vecsort-selfselect",
  "summary": "在 kernel Init 中把 useVectorSortT2_ self-select 门控收窄为仅 bf16 整行 Sort 几何（T==bfloat16_t 且整行可驻留），激活既有 GatherCompactSlotsVF + VectorSortSelectTopKT2 整行 AscendC::Sort 路径；fp16 等其他 dtype 明确留在标量有界堆（round-4 实证回归）。",
  "verification": {
    "correctness": [
      "verify 12/12 通过；非 bf16 逐字节回退标量堆",
      "case_18 官方路径 spot_check 868.9us 可复现（measure 877.7us）"
    ],
    "performance": [
      "case_18 12270us -> 877.7us（measure）≈13.98x / 868.9us（official-path）≈14x",
      "case_20 cumulative 1.006x unchanged（round-4 回归被规避）",
      "score_model 边际 +0.0605 官方 pts（estimate）"
    ],
    "rollback_signals": [
      "fp16 等被误导入向量路径回归即收紧 gate",
      "spot_check verdict=not_reproducible 时回退"
    ]
  }
}
-->

# 性能优化策略：bf16 受限 T2-ES1 整行向量排序 self-select

单一优化点：在 kernel Init 中把 useVectorSortT2_ self-select 门控收窄为仅 bf16 整行 Sort 几何（T==bfloat16_t 且整行可驻留），激活既有 GatherCompactSlotsVF + VectorSortSelectTopKT2 整行 AscendC::Sort 路径；fp16 等其他 dtype 明确留在标量有界堆（round-4 实证回归）。

## 1. 原理

同一向量代码路径对不同 dtype/geometry 收益方向不同：bf16 走整行 AscendC::Sort（非 radix）在 sortLen<=256 的整行几何下净收益巨大（14x），而 fp16 走 RADIX_SELECT 在同区间回归 2x。把 self-select gate 收窄到经验证的单 dtype 几何，可同时拿到收益与避开回归。

实现机制：Init 中解码运行时字段后设 useVectorSortT2_=1，门控 ROUTE==2 && axisBlockLen_>1 && chunkCount_==1 && T==bfloat16_t && sortLen∈[128,4096] 且整行 Sort UB 可驻留；fp16/half 显式排除（round-4 实证 2x 回归）；不匹配逐字节回退标量堆。

## 2. 性能问题模式

- 优化目标：为 case_18（bf16 [255,8193] k=128 dim=0 largest=false，baseline 官方 12290us 标量堆）激活已验证的向量整行 Sort 路径，同时规避 round-4 的 fp16 回归（case_20 必须保持标量堆）。
- 适用数据流：TopK T2 Q>1 ES1（chunkCount==1 整行）且 dtype==bfloat16_t 的 case：非 radix key 走整行 AscendC::Sort 路径，官方路径收益可复现（case_18 sortLen=255 k=128）。
- Feature signature：`{"bottleneck": ["scalar-bounded-heap-when-vector-path-latent", "t2-scalar-heap"], "dtypes": ["bf16"], "pattern": "bf16-restricted-t2-es1-vecsort-selfselect", "reduce_mode": "top-k", "structure": ["t2-q1-es1-whole-row", "gather-compact-slots-vf", "whole-row-ascendc-sort"]}`

## 3. 正确性红线

- 放宽 dtype 集合会重新引入 round-4 的 fp16 回归
- bf16 整行 Sort 的 UB/LCM 预算在不同 sortLen 下需复核
- 依赖宿主 tiling 字段不生效的前提（后续 host 修复会改变条件）

资源与硬件约束：

- gate 必须同时约束 dtype（bf16-only）与 geometry（整行/chunkCount==1）
- 任何放宽 dtype 的尝试都必须先对目标 case 官方路径 spot_check

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- T2 Q>1 ES1（chunkCount==1 整行）、dtype==bfloat16_t
- sortLen 在 [128,4096] 且整行向量 Sort 的 UB/LCM 预算可容纳
- 非 radix key（bf16）整行 AscendC::Sort 路径存在且已验证

不适用：

- fp16/half 及 radix key——实证在 sortLen=511 k=100 下向量路径 ~2x 回归
- sortLen>256 的其他 dtype（沿用 topk-t2-gather-vector-select 的 sortLen<=256 排除）
- 多 chunk（chunkCount>1）大轴——走 chunked-vector-sort-merge

## 5. 实施步骤

1. 确认 case_18 运行时 geometry（T2 Q>1 ES1、bf16、sortLen=255）
2. 在 Init 添加 bf16-only useVectorSortT2_ self-select（放在缓冲分配前）
3. fp16 等其他 dtype 保持标量堆（round-4 教训）
4. verify 全量 + case_18/case_20 官方路径 spot_check

## 6. LLM 前置问题

- 目标实现是否满足：T2 Q>1 ES1（chunkCount==1 整行）、dtype==bfloat16_t？
- 目标实现是否满足：sortLen 在 [128,4096] 且整行向量 Sort 的 UB/LCM 预算可容纳？
- 目标实现是否满足：非 radix key（bf16）整行 AscendC::Sort 路径存在且已验证？
- 是否命中排除条件：fp16/half 及 radix key——实证在 sortLen=511 k=100 下向量路径 ~2x 回归？

## 7. 验收标准

正确性：

- verify 12/12 通过；非 bf16 逐字节回退标量堆
- case_18 官方路径 spot_check 868.9us 可复现（measure 877.7us）

性能：

- case_18 12270us -> 877.7us（measure）≈13.98x / 868.9us（official-path）≈14x
- case_20 cumulative 1.006x unchanged（round-4 回归被规避）
- score_model 边际 +0.0605 官方 pts（estimate）

回滚信号：

- fp16 等被误导入向量路径回归即收紧 gate
- spot_check verdict=not_reproducible 时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize

- top_k-20260831_151225-dbf26e（round=5, status=accepted）

## 检索卡（短卡）

动作：把 useVectorSortT2_ self-select 门控收窄为仅 bf16 整行 Sort 几何，fp16 等明确留在标量堆。
适用：T2 Q>1 ES1（chunkCount==1）且 dtype==bfloat16_t；sortLen∈[128,4096]。
限制：放宽 dtype 集合会重新引入 fp16 回归；gate 须同时约束 dtype 与 geometry。
范围：TopK T2 Q>1 ES1 整行 case 的路径自选择
检索词：useVectorSortT2_、GatherCompactSlotsVF、VectorSortSelectTopKT2、AscendC::Sort
机会：bf16 sortLen=255 k=128 的 baseline 官方耗时上万微秒走标量有界堆
代价：依赖宿主 tiling 字段不生效的前提，host 修复后条件会改变
