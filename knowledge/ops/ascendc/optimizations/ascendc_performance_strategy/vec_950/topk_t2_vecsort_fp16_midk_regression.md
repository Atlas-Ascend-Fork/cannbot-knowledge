---
type: Optimization
title: T2-ES1 向量排序 self-select 门控过宽导致 fp16 中 k 段回归
description: T2 Q>1 ES1 向量排序 self-select 的 gate 须同时收紧 dtype 与 sortLen（sortLen<=256），禁只按 dtype 放行。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-t2-vecsort-fp16-midk-regression.md
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
      "self-select gate 必须同时约束 dtype 与 sortLen（sortLen<=256）",
      "跨 dtype/geometry 复用前必须对每个目标 case 做官方路径 spot_check"
    ],
    "excluded_conditions": [
      "sortLen>256 且 k/sortLen 小（如 fp16 sortLen=511 k=100）——向量路径回归",
      "int/int8 或 sortLen 超支持区间"
    ],
    "required_conditions": [
      "T2 Q>1 ES1 整行（chunkCount==1）case，dtype 在向量路径支持集内",
      "sortLen 处于 [128, 4096] 门控区间（会命中过宽 gate）"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "comparison_sha256": "83750b74d6d5ce5fd7923fcdb99551093fca842c37e084930797164159574ab4",
      "decision_sha256": "ae10849efee04f3891418eb673d34f8468bc138be87417a98e46714758cc8dce",
      "operator_class": "sort-select",
      "performance_sha256": "d1e2d1e941f25aa4c5ef8d54c6f083ce3809eb6807368962d8b7a40f0e461904",
      "round": 4,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "a92a5ea443908100788f91a881c335bf2857f8adfe428b9aba587ec6b6baac83",
      "verify_sha256": "37fa154ba73862278f8845918d703536be02b53598d409c508e5369d490126e6"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vector-sort-fixed-overhead-not-amortized"
    ],
    "dtypes": [
      "fp16"
    ],
    "pattern": "t2-es1-vecsort-dtype-sortlen-boundary",
    "reduce_mode": "top-k",
    "structure": [
      "t2-q1-es1-whole-row",
      "gather-compact-slots-vf",
      "vector-sort-select-t2"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-T2-VECSORT-FP16-MIDK-REGRESSION",
  "implementation_steps": [
    "确认目标 case 的 sortLen/k/dtype 组合",
    "对每个候选 geometry 做 probe：激活向量路径并官方路径 spot_check 对比标量堆",
    "只保留官方路径可复现收益的 geometry 进 gate"
  ],
  "intent": "记录 T2-ES1 向量路径的负边界：哪些 geometry 下激活它会产生真实回归（避免后续 run 重复踩坑）。",
  "mechanism": "round-4 在 Init 设 useVectorSortT2_=1，门控 ROUTE==2 && axisBlockLen_>1 && chunkCount_==1 && sortLen∈[128,4096] && dtype∈{half,bfloat16_t,float,int32_t} && useVectorSortT2_==0；case_18/20 同时命中，case_20 走 GatherCompactSlotsVF + VectorSortSelectTopKT2（fp16 RADIX_SELECT）后官方路径 850.4us（baseline 439.8us）。",
  "name": "T2-ES1 向量排序 self-select 门控过宽导致 fp16 中 k 段回归",
  "operator_class": "sort-select",
  "operator_scope": "TopK T2 Q>1 ES1（chunkCount==1 整行）case 上激活 GatherCompactSlotsVF + VectorSortSelectTopKT2 向量路径时的 dtype×sortLen 边界。",
  "principle": "向量整行排序的固定开销（Gather 压实 + 整行 Sort）对 sortLen 敏感；当 sortLen 较大（>256）且 k/sortLen 较小（0.2）时，标量有界堆的每行成本更低，向量路径的恒定压缩/排序开销无法摊薄，净效果为回归。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize"
  ],
  "risks": [
    "只看 measure 结果忽略官方路径差异会误判（measure 噪声）",
    "gate 收紧后漏掉本可收益的 bf16 整行 Sort 几何（见 round-5 修复）"
  ],
  "slug": "topk-t2-vecsort-fp16-midk-regression",
  "summary": "对 T2 Q>1 ES1 向量排序路径做 in-kernel self-select 时，门控若只按 dtype 集合（half/bf16/float/int32）与 sortLen∈[128,4096] 放行，会把 fp16 sortLen=511 k=100（k/sortLen=0.2）的 case 也导入向量路径，结果该路径比标量有界堆 ~2x 更慢（850us vs 440us）。边界：向量整行排序只在 sortLen<=256 的整行/中轴几何下胜出。",
  "verification": {
    "correctness": [
      "verify 通过（12/12）——正确性无问题，问题在性能",
      "case_20 回归官方路径 850.4us 可复现，非测量漂移"
    ],
    "performance": [
      "case_18 +14.0x（bf16 sortLen=255）但 case_20 -2x（fp16 sortLen=511）",
      "净官方分 ~0（+0.0607 -0.0609）；decision=rejected"
    ],
    "rollback_signals": [
      "任何 case 在向量路径上相对标量堆真实回归即拒绝并回退"
    ]
  }
}
-->

# 性能优化策略：T2-ES1 向量排序 self-select 门控过宽导致 fp16 中 k 段回归

单一优化点：对 T2 Q>1 ES1 向量排序路径做 in-kernel self-select 时，门控若只按 dtype 集合（half/bf16/float/int32）与 sortLen∈[128,4096] 放行，会把 fp16 sortLen=511 k=100（k/sortLen=0.2）的 case 也导入向量路径，结果该路径比标量有界堆 ~2x 更慢（850us vs 440us）。边界：向量整行排序只在 sortLen<=256 的整行/中轴几何下胜出。

## 1. 原理

向量整行排序的固定开销（Gather 压实 + 整行 Sort）对 sortLen 敏感；当 sortLen 较大（>256）且 k/sortLen 较小（0.2）时，标量有界堆的每行成本更低，向量路径的恒定压缩/排序开销无法摊薄，净效果为回归。

实现机制：round-4 在 Init 设 useVectorSortT2_=1，门控 ROUTE==2 && axisBlockLen_>1 && chunkCount_==1 && sortLen∈[128,4096] && dtype∈{half,bfloat16_t,float,int32_t} && useVectorSortT2_==0；case_18/20 同时命中，case_20 走 GatherCompactSlotsVF + VectorSortSelectTopKT2（fp16 RADIX_SELECT）后官方路径 850.4us（baseline 439.8us）。

## 2. 性能问题模式

- 优化目标：记录 T2-ES1 向量路径的负边界：哪些 geometry 下激活它会产生真实回归（避免后续 run 重复踩坑）。
- 适用数据流：TopK T2 Q>1 ES1（chunkCount==1 整行）case 上激活 GatherCompactSlotsVF + VectorSortSelectTopKT2 向量路径时的 dtype×sortLen 边界。
- Feature signature：`{"bottleneck": ["vector-sort-fixed-overhead-not-amortized"], "dtypes": ["fp16"], "pattern": "t2-es1-vecsort-dtype-sortlen-boundary", "reduce_mode": "top-k", "structure": ["t2-q1-es1-whole-row", "gather-compact-slots-vf", "vector-sort-select-t2"]}`

## 3. 正确性红线

- 只看 measure 结果忽略官方路径差异会误判（measure 噪声）
- gate 收紧后漏掉本可收益的 bf16 整行 Sort 几何（见 round-5 修复）

资源与硬件约束：

- self-select gate 必须同时约束 dtype 与 sortLen（sortLen<=256）
- 跨 dtype/geometry 复用前必须对每个目标 case 做官方路径 spot_check

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- T2 Q>1 ES1 整行（chunkCount==1）case，dtype 在向量路径支持集内
- sortLen 处于 [128, 4096] 门控区间（会命中过宽 gate）

不适用：

- sortLen>256 且 k/sortLen 小（如 fp16 sortLen=511 k=100）——向量路径回归
- int/int8 或 sortLen 超支持区间

## 5. 实施步骤

1. 确认目标 case 的 sortLen/k/dtype 组合
2. 对每个候选 geometry 做 probe：激活向量路径并官方路径 spot_check 对比标量堆
3. 只保留官方路径可复现收益的 geometry 进 gate

## 6. LLM 前置问题

- 目标实现是否满足：T2 Q>1 ES1 整行（chunkCount==1）case，dtype 在向量路径支持集内？
- 目标实现是否满足：sortLen 处于 [128, 4096] 门控区间（会命中过宽 gate）？
- 是否命中排除条件：sortLen>256 且 k/sortLen 小（如 fp16 sortLen=511 k=100）——向量路径回归？

## 7. 验收标准

正确性：

- verify 通过（12/12）——正确性无问题，问题在性能
- case_20 回归官方路径 850.4us 可复现，非测量漂移

性能：

- case_18 +14.0x（bf16 sortLen=255）但 case_20 -2x（fp16 sortLen=511）
- 净官方分 ~0（+0.0607 -0.0609）；decision=rejected

回滚信号：

- 任何 case 在向量路径上相对标量堆真实回归即拒绝并回退

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize

- top_k-20260831_151225-dbf26e（round=4, status=rejected）

## 检索卡（短卡）

动作：T2 Q>1 ES1 向量排序 self-select 的 gate 须同时收紧 dtype 与 sortLen（sortLen<=256），禁只按 dtype 放行。
适用：T2 Q>1 ES1 整行（chunkCount==1）且 sortLen 命中 [128,4096] 过宽门控区间时。
限制：fp16 sortLen=511 k=100（k/sortLen=0.2）导入向量路径后官方 850.4us vs 439.8us，约 2x 更慢。
范围：T2 Q>1 ES1 整行向量排序路径的 dtype×sortLen 门控
检索词：useVectorSortT2_、GatherCompactSlotsVF、VectorSortSelectTopKT2、sortLen<=256
机会：向量整行排序的压实与 Sort 固定开销在 sortLen 大、k 小时无法摊薄
代价：整轮 rejected（净官方分 ~0）
