---
type: Optimization
title: TopK 稳态的最差候选缓存
description: 缓存候选集合最差项，让 TopK 稳态的大多数输入以 O(1) 快速拒绝。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cached-worst-candidate.md
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
      "缓存的最差值与索引必须在每次候选集合变化后同步刷新",
      "比较器必须完整编码 largest/smallest、sorted、NaN 与并列索引规则"
    ],
    "excluded_conditions": [
      "k 很大、替换频繁导致每次 O(k) 重扫仍占主导时应使用有界堆或更强算法",
      "候选集合不能常驻 UB，或比较语义不允许缓存单一最差候选时不适用"
    ],
    "required_conditions": [
      "TopK 以 UB 常驻候选数组维护结果，当前稳态为每个输入线性搜索最差候选",
      "多数输入可通过与当前最差候选的一次比较直接拒绝",
      "k 和候选数组大小满足 UB 预算"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "case": "validated-subset",
      "operator_class": "sort-select",
      "precision": "validated subset PASS; final path 20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/top_k_opt_20260820.md",
      "speedup": "2.21-11.93",
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "candidate-linear-scan",
      "steady-state-selection"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "cached-worst-candidate",
    "reduce_mode": "top-k",
    "structure": [
      "candidate-cache",
      "fast-reject",
      "ub-resident"
    ]
  },
  "gain": "有效子集 case_1 11.24x、case_3 11.93x、case_5 6.01x、case_6 3.39x、case_12 2.21x。",
  "generality": "op_class",
  "id": "TOPK-CACHED-WORST",
  "implementation_steps": [
    "把候选构建显式拆成未填满阶段与填满后的稳态阶段",
    "候选填满时扫描一次得到当前最差候选及位置，并将其缓存在标量或寄存器",
    "稳态对每个输入先做一次 O(1) 比较，只有胜过最差候选时才替换",
    "替换后重新扫描 k 个候选刷新最差缓存，finalize 继续使用已验证排序路径",
    "为大 k 或高替换率设置切换到有界堆的边界"
  ],
  "intent": "避免 TopK 候选数组填满后仍为每个输入执行 O(k) 的最差候选搜索。",
  "mechanism": "候选未填满时直接追加；填满后缓存当前最差值与位置，大多数输入用一次比较快速拒绝，仅在替换发生时重新扫描候选数组更新缓存。",
  "name": "TopK 稳态的最差候选缓存",
  "op": "top_k",
  "operator_class": "sort-select",
  "operator_scope": "候选集合常驻 UB、k 中小且稳态替换率较低的流式 TopK 选择",
  "principle": "TopK 稳态中绝大多数输入不会进入候选集；缓存当前淘汰阈值可把常见拒绝路径从 O(k) 降为 O(1)，只让少数真实替换承担重扫成本。",
  "provenance": {
    "source_report": "<PERF_ROOT>/strategies/top_k_opt_20260820.md"
  },
  "related_anti_patterns": [],
  "risks": [
    "替换后遗漏刷新缓存会造成后续候选错误",
    "高替换率或大 k 下 O(k) 重扫和 O(k²) finalize 仍可能成为瓶颈"
  ],
  "schema_version": 2,
  "slug": "cached-worst-candidate",
  "source": "external_verified",
  "status": "applied",
  "summary": "缓存候选集合最差项，让 TopK 稳态的大多数输入以 O(1) 快速拒绝。",
  "verification": {
    "correctness": [
      "覆盖 k=1、k 接近轴长、全相等、重复值、NaN、largest/smallest 与 sorted 组合，并核对稳定索引规则"
    ],
    "performance": [
      "统计替换率和每元素比较次数，在低/高替换分布与不同 k 上确认收益边界"
    ],
    "rollback_signals": [
      "缓存失配、并列语义错误，或高替换率/大 k 形状稳定回归时切换有界堆或回退"
    ]
  }
}
-->

# 性能优化策略：TopK 稳态的最差候选缓存

单一优化点：缓存候选集合最差项，让 TopK 稳态的大多数输入以 O(1) 快速拒绝。

## 1. 原理

TopK 稳态中绝大多数输入不会进入候选集；缓存当前淘汰阈值可把常见拒绝路径从 O(k) 降为 O(1)，只让少数真实替换承担重扫成本。

实现机制：候选未填满时直接追加；填满后缓存当前最差值与位置，大多数输入用一次比较快速拒绝，仅在替换发生时重新扫描候选数组更新缓存。

## 2. 性能问题模式

- 优化目标：避免 TopK 候选数组填满后仍为每个输入执行 O(k) 的最差候选搜索。
- 适用数据流：候选集合常驻 UB、k 中小且稳态替换率较低的流式 TopK 选择
- Feature signature：`{"bottleneck": ["candidate-linear-scan", "steady-state-selection"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "cached-worst-candidate", "reduce_mode": "top-k", "structure": ["candidate-cache", "fast-reject", "ub-resident"]}`

## 3. 正确性红线

- 替换后遗漏刷新缓存会造成后续候选错误
- 高替换率或大 k 下 O(k) 重扫和 O(k²) finalize 仍可能成为瓶颈

资源与硬件约束：

- 缓存的最差值与索引必须在每次候选集合变化后同步刷新
- 比较器必须完整编码 largest/smallest、sorted、NaN 与并列索引规则

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- TopK 以 UB 常驻候选数组维护结果，当前稳态为每个输入线性搜索最差候选
- 多数输入可通过与当前最差候选的一次比较直接拒绝
- k 和候选数组大小满足 UB 预算

不适用：

- k 很大、替换频繁导致每次 O(k) 重扫仍占主导时应使用有界堆或更强算法
- 候选集合不能常驻 UB，或比较语义不允许缓存单一最差候选时不适用

## 5. 实施步骤

1. 把候选构建显式拆成未填满阶段与填满后的稳态阶段
2. 候选填满时扫描一次得到当前最差候选及位置，并将其缓存在标量或寄存器
3. 稳态对每个输入先做一次 O(1) 比较，只有胜过最差候选时才替换
4. 替换后重新扫描 k 个候选刷新最差缓存，finalize 继续使用已验证排序路径
5. 为大 k 或高替换率设置切换到有界堆的边界

## 6. LLM 前置问题

- 目标实现是否满足：TopK 以 UB 常驻候选数组维护结果，当前稳态为每个输入线性搜索最差候选？
- 目标实现是否满足：多数输入可通过与当前最差候选的一次比较直接拒绝？
- 目标实现是否满足：k 和候选数组大小满足 UB 预算？
- 是否命中排除条件：k 很大、替换频繁导致每次 O(k) 重扫仍占主导时应使用有界堆或更强算法？

## 7. 验收标准

正确性：

- 覆盖 k=1、k 接近轴长、全相等、重复值、NaN、largest/smallest 与 sorted 组合，并核对稳定索引规则

性能：

- 统计替换率和每元素比较次数，在低/高替换分布与不同 k 上确认收益边界

回滚信号：

- 缓存失配、并列语义错误，或高替换率/大 k 形状稳定回归时切换有界堆或回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- strategy-top-k-20260820-topk-001（status=accepted, case=validated-subset, speedup=2.21-11.93）

## 检索卡（短卡）

动作：缓存当前最差候选及位置，将稳态拒绝由每次O(k)搜索改为一次O(1)比较，仅替换后重扫。
适用：TopK以UB常驻候选数组维护结果，稳态对每个输入线性寻找最差候选。
限制：候选集合每次变化后，必须同步刷新缓存的最差值、索引或位置。
范围：selection-sort/top-k的UB常驻候选数组稳态。
检索词：TopK、UB常驻候选数组、淘汰阈值、最差值、最差位置、O(k)重扫
机会：候选数组填满后，仍对每个输入执行O(k)最差候选搜索。
代价：高替换率或大k时仍需频繁承担O(k)重扫。
