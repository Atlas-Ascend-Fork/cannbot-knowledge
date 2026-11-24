---
type: Optimization
title: TopK 稳态向量批量拒绝预过滤
description: 把稳态中被 cachedRoot（最差候选）逐元素标量拒绝的绝大多数输入改为每 64 元素一条向量比较 vs 广播 cachedRoot，整批无胜者直接跳过，削减 AIV Scalar 逐元素工作量。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-vector-batched-reject.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "向量比较 32B 对齐；批内越界需掩码（LoadAlign DATA_BLOCK_COPY）避免 507035",
      "比较器须完整编码 largest/smallest、NaN 与并列索引规则"
    ],
    "excluded_conditions": [
      "T2 路由槽区 strided 布局（需先 free compaction，见 topk-t2-gather-vector-select）",
      "k 极低/行短、批量收益被门控排除的 case"
    ],
    "required_conditions": [
      "稳态阶段每个输入与当前最差候选 cachedRoot 比较即能拒绝大多数元素",
      "行内数据连续（stride==1）且 64-lane 批量可一次覆盖",
      "k*256 <= inputLen（门控）且 dtype∈{half,bf16,float}"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "incremental 1.1937x; case_1 13.39x, case_14 10.22x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "f897dc5037580f5ab90ef6f0231587175a023e569c0ba94e31585022c7b783ca",
      "decision_sha256": "0de6c8ed07a123945bca322cbcf08732f0bf4f4c690573b6354bdacf05eb55b3",
      "operator_class": "sort-select",
      "performance_sha256": "75d3fa6c507ac9fe86a6598a9687a45776095ee8ca27f11179ccaf8b99669457",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "28e507d99e2a02e9fc280705c47c93df127d9a141162f2e66756dbca58a1fd14",
      "verify_sha256": "c31989ba0c07152aaffa0666ca9cb4b5e8afe4026bd7d6e61573aae6910d9961"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "candidate-linear-scan",
      "steady-state-selection",
      "scalar-heap-maintenance"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "vector-batched-reject",
    "reduce_mode": "top-k",
    "structure": [
      "simd-batch-reject",
      "cached-worst-candidate",
      "ub-resident"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-VECTOR-BATCHED-REJECT",
  "implementation_steps": [
    "稳态循环每 64 元素向量加载并广播 cachedRoot",
    "一条向量比较，整批无胜者 → continue（零标量逐元素工作）",
    "有胜者时回落逐元素进有界堆并刷新 cachedRoot"
  ],
  "intent": "消除 baseline 全部 20 case 的 AIV Scalar 引擎逐元素有界堆维护（aiv_scalar 93.4-100%、aiv_vec 0）。",
  "mechanism": "每 64 元素一条向量 compare vs 广播 cachedRoot（标量/Reg 广播）；整批无胜者 → 整批跳过（不逐元素进堆）；有胜者才逐元素进有界堆。保留精确比较（无假阴性）。",
  "name": "TopK 稳态向量批量拒绝预过滤",
  "operator_class": "sort-select",
  "operator_scope": "TopK ComputeTopK 稳态：行内候选有界堆已填满、cachedRoot 能一次拒绝绝大多数输入、行连续 stride==1 且 k*256<=inputLen、dtype∈{half,bf16,float}",
  "principle": "cachedRoot 拒绝大多数输入；把该比较从逐元素标量提升为 SIMD 批量比较，用向量引擎替代标量引擎执行主导的拒绝决策。",
  "related_anti_patterns": [
    "scalar-steady-state-linear-scan"
  ],
  "risks": [
    "批内部分胜者时仍需逐元素处理（头寸保留）",
    "门控外 case 保持原路径逐字节不变（无增益无回归）"
  ],
  "slug": "topk-vector-batched-reject",
  "summary": "把稳态中被 cachedRoot（最差候选）逐元素标量拒绝的绝大多数输入改为每 64 元素一条向量比较 vs 广播 cachedRoot，整批无胜者直接跳过，削减 AIV Scalar 逐元素工作量。",
  "verification": {
    "correctness": [
      "verify 20/20 通过，多轮稳定"
    ],
    "performance": [
      "case_1 13.39×、case_14 10.22×，incremental 1.1937×，regressed=0；管道 aiv_scalar -95%"
    ],
    "rollback_signals": [
      "门控外 case 回归或 aiv_scalar 不降则回退"
    ]
  }
}
-->

# 性能优化策略：TopK 稳态向量批量拒绝预过滤

单一优化点：把稳态中被 cachedRoot（最差候选）逐元素标量拒绝的绝大多数输入改为每 64 元素一条向量比较 vs 广播 cachedRoot，整批无胜者直接跳过，削减 AIV Scalar 逐元素工作量。

## 1. 原理

cachedRoot 拒绝大多数输入；把该比较从逐元素标量提升为 SIMD 批量比较，用向量引擎替代标量引擎执行主导的拒绝决策。

实现机制：每 64 元素一条向量 compare vs 广播 cachedRoot（标量/Reg 广播）；整批无胜者 → 整批跳过（不逐元素进堆）；有胜者才逐元素进有界堆。保留精确比较（无假阴性）。

## 2. 性能问题模式

- 优化目标：消除 baseline 全部 20 case 的 AIV Scalar 引擎逐元素有界堆维护（aiv_scalar 93.4-100%、aiv_vec 0）。
- 适用数据流：TopK ComputeTopK 稳态：行内候选有界堆已填满、cachedRoot 能一次拒绝绝大多数输入、行连续 stride==1 且 k*256<=inputLen、dtype∈{half,bf16,float}
- Feature signature：`{"bottleneck": ["candidate-linear-scan", "steady-state-selection", "scalar-heap-maintenance"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "vector-batched-reject", "reduce_mode": "top-k", "structure": ["simd-batch-reject", "cached-worst-candidate", "ub-resident"]}`

## 3. 正确性红线

- 批内部分胜者时仍需逐元素处理（头寸保留）
- 门控外 case 保持原路径逐字节不变（无增益无回归）

资源与硬件约束：

- 向量比较 32B 对齐；批内越界需掩码（LoadAlign DATA_BLOCK_COPY）避免 507035
- 比较器须完整编码 largest/smallest、NaN 与并列索引规则

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 稳态阶段每个输入与当前最差候选 cachedRoot 比较即能拒绝大多数元素
- 行内数据连续（stride==1）且 64-lane 批量可一次覆盖
- k*256 <= inputLen（门控）且 dtype∈{half,bf16,float}

不适用：

- T2 路由槽区 strided 布局（需先 free compaction，见 topk-t2-gather-vector-select）
- k 极低/行短、批量收益被门控排除的 case

## 5. 实施步骤

1. 稳态循环每 64 元素向量加载并广播 cachedRoot
2. 一条向量比较，整批无胜者 → continue（零标量逐元素工作）
3. 有胜者时回落逐元素进有界堆并刷新 cachedRoot

## 6. LLM 前置问题

- 目标实现是否满足：稳态阶段每个输入与当前最差候选 cachedRoot 比较即能拒绝大多数元素？
- 目标实现是否满足：行内数据连续（stride==1）且 64-lane 批量可一次覆盖？
- 目标实现是否满足：k*256 <= inputLen（门控）且 dtype∈{half,bf16,float}？
- 是否命中排除条件：T2 路由槽区 strided 布局（需先 free compaction，见 topk-t2-gather-vector-select）？

## 7. 验收标准

正确性：

- verify 20/20 通过，多轮稳定

性能：

- case_1 13.39×、case_14 10.22×，incremental 1.1937×，regressed=0；管道 aiv_scalar -95%

回滚信号：

- 门控外 case 回归或 aiv_scalar 不降则回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-steady-state-linear-scan

- top_k-20260828_120811-77cf84（round=1, status=accepted, speedup=incremental 1.1937x; case_1 13.39x, case_14 10.22x）
- top_k-20260828_120811-77cf84（round=1, status=accepted）

## 检索卡（短卡）

动作：将逐元素拒绝比较改为每64元素向量比较cachedRoot；无胜者整批跳过，有胜者回落逐元素入堆。
适用：稳态中cachedRoot可拒绝多数元素，且行连续、stride==1并可由64-lane批次覆盖。
限制：向量比较32B对齐，尾批掩码；有胜者逐元素入堆并刷新cachedRoot；门控外保持原路径。
范围：selection-sort-top-k的TopK稳态候选堆循环。
检索词：cachedRoot，SIMD批量比较，64-lane，整批拒绝，有界堆回落
机会：TopK稳态逐元素维护有界堆，且cachedRoot能够拒绝大多数输入。
