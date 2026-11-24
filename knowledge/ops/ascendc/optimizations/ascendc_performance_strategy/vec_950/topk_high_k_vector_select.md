---
type: Optimization
title: 高 k/sortLen 整行向量排序选择快路径
description: 对高 k/sortLen（>=0.2）整行驻留 UB 的行，用 AIV 向量引擎整行排序（AscendC::Sort RADIX）后截取前 k（值+索引），替代标量有界堆 fill+稳态+finalize 三段标量工作。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-high-k-vector-select.md
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
      "NaN fp 输入会排到对端（假设性；目标 case 无 NaN）",
      "UB 峰值估算须 <= ubSize，否则回退标量路径"
    ],
    "excluded_conditions": [
      "int64/int8/int32、低 k（<0.2）、非末轴 chunk 场景",
      "排序要求全局稳定且比较器不能由 RADIX 表达"
    ],
    "required_conditions": [
      "整行可驻留 UB 且 k/sortLen>=0.2",
      "dtype∈{half,bf16,float}，行连续",
      "k 值+索引可整行向量排序输出"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "incremental 1.103x; case_11 30.14x, case_12 34.67x, case_17 29.95x, case_19 22.27x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "684742e7a9846a0daf3c0afa6da9b5677b83eca5e7c1975373eeed085ee86c86",
      "decision_sha256": "7cf043bbdd881819e7ca0a5b095c01260633b2108f204647cd8a57922bd6c290",
      "operator_class": "sort-select",
      "performance_sha256": "dcb71b7c795290e72ca1a4bd83c4c236475973b221b1032b49f0192d6ac31c6c",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "0b5ce2b514ae5d05bc97f6c3e0071a9058530f96ae70785d2fdb5e1e4605a532",
      "verify_sha256": "c66a5ec8d4b7d64ecad490cd222f6d50d4716c9bbd980bdbec01386bf323725e"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bounded-heap",
      "quadratic-finalize",
      "fill-sift-up"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "high-k-vector-select",
    "reduce_mode": "top-k",
    "structure": [
      "whole-row-vector-sort",
      "radix-select",
      "ub-resident"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-HIGH-K-VECTOR-SELECT",
  "implementation_steps": [
    "门控判定 k/sortLen 与 UB 预算",
    "整行向量 RADIX 排序（AscendC::Sort）",
    "截取前 k 值+索引写输出"
  ],
  "intent": "消除高 k 场景标量有界堆的 fill（O(k log k) sift-up）与 finalize（O(k log k) 堆排）标量成本。",
  "mechanism": "整行驻留 UB → 单次向量 RADIX sort/select → 直接取前 k 值+索引；门控 k/sortLen>=0.2、UB 峰值<=ubSize、dtype∈{half,bf16,float}；非门控 case 保持标量堆路径逐字节不变。",
  "name": "高 k/sortLen 整行向量排序选择快路径",
  "operator_class": "sort-select",
  "operator_scope": "TopK T1 ES1（dim==末轴、chunkLen==0、整行驻留 UB）且 k/sortLen>=0.2 的 case",
  "principle": "整行一次向量排序的 AIV 引擎成本远低于逐元素标量堆维护 + 二次 finalize。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize"
  ],
  "risks": [
    "NaN 排序语义边界（未在目标 case 触发）",
    "非门控 case 必须逐字节不变（control 全 ~1.0×）"
  ],
  "slug": "topk-high-k-vector-select",
  "summary": "对高 k/sortLen（>=0.2）整行驻留 UB 的行，用 AIV 向量引擎整行排序（AscendC::Sort RADIX）后截取前 k（值+索引），替代标量有界堆 fill+稳态+finalize 三段标量工作。",
  "verification": {
    "correctness": [
      "verify 20/20 通过"
    ],
    "performance": [
      "case_11 30.14×、case_12 34.67×、case_17 29.95×、case_19 22.27×，incremental 1.103×，regressed=0"
    ],
    "rollback_signals": [
      "任何非门控 case 回归则回退"
    ]
  }
}
-->

# 性能优化策略：高 k/sortLen 整行向量排序选择快路径

单一优化点：对高 k/sortLen（>=0.2）整行驻留 UB 的行，用 AIV 向量引擎整行排序（AscendC::Sort RADIX）后截取前 k（值+索引），替代标量有界堆 fill+稳态+finalize 三段标量工作。

## 1. 原理

整行一次向量排序的 AIV 引擎成本远低于逐元素标量堆维护 + 二次 finalize。

实现机制：整行驻留 UB → 单次向量 RADIX sort/select → 直接取前 k 值+索引；门控 k/sortLen>=0.2、UB 峰值<=ubSize、dtype∈{half,bf16,float}；非门控 case 保持标量堆路径逐字节不变。

## 2. 性能问题模式

- 优化目标：消除高 k 场景标量有界堆的 fill（O(k log k) sift-up）与 finalize（O(k log k) 堆排）标量成本。
- 适用数据流：TopK T1 ES1（dim==末轴、chunkLen==0、整行驻留 UB）且 k/sortLen>=0.2 的 case
- Feature signature：`{"bottleneck": ["scalar-bounded-heap", "quadratic-finalize", "fill-sift-up"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "high-k-vector-select", "reduce_mode": "top-k", "structure": ["whole-row-vector-sort", "radix-select", "ub-resident"]}`

## 3. 正确性红线

- NaN 排序语义边界（未在目标 case 触发）
- 非门控 case 必须逐字节不变（control 全 ~1.0×）

资源与硬件约束：

- NaN fp 输入会排到对端（假设性；目标 case 无 NaN）
- UB 峰值估算须 <= ubSize，否则回退标量路径

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 整行可驻留 UB 且 k/sortLen>=0.2
- dtype∈{half,bf16,float}，行连续
- k 值+索引可整行向量排序输出

不适用：

- int64/int8/int32、低 k（<0.2）、非末轴 chunk 场景
- 排序要求全局稳定且比较器不能由 RADIX 表达

## 5. 实施步骤

1. 门控判定 k/sortLen 与 UB 预算
2. 整行向量 RADIX 排序（AscendC::Sort）
3. 截取前 k 值+索引写输出

## 6. LLM 前置问题

- 目标实现是否满足：整行可驻留 UB 且 k/sortLen>=0.2？
- 目标实现是否满足：dtype∈{half,bf16,float}，行连续？
- 目标实现是否满足：k 值+索引可整行向量排序输出？
- 是否命中排除条件：int64/int8/int32、低 k（<0.2）、非末轴 chunk 场景？

## 7. 验收标准

正确性：

- verify 20/20 通过

性能：

- case_11 30.14×、case_12 34.67×、case_17 29.95×、case_19 22.27×，incremental 1.103×，regressed=0

回滚信号：

- 任何非门控 case 回归则回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize

- top_k-20260828_120811-77cf84（round=3, status=accepted, speedup=incremental 1.103x; case_11 30.14x, case_12 34.67x, case_17 29.95x, case_19 22.27x）
- top_k-20260828_120811-77cf84（round=3, status=accepted）

## 检索卡（短卡）

动作：将逐元素标量堆维护与堆排改为整行驻留UB、单次向量RADIX排序/选择，直接截取前k值和索引。
适用：整行可驻留UB、k/sortLen≥0.2，且行连续、dtype为half/bf16/float。
限制：验证NaN排序与比较器契约、核对UB峰值；非门控路径代码及数值行为保持不变。
范围：selection-sort-top-k的TopK T1 ES1末轴路径。
检索词：高k，k/sortLen，整行驻留UB，RADIX sort/select，AscendC::Sort
机会：高k路径仍有fill的sift-up及finalize堆排等O(k log k)标量工作。
