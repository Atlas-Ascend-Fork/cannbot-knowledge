---
type: Optimization
title: T2 向量 Gather free-compaction + 整行向量选择
description: 对 T2 Q>1 中轴 case 用向量 Reg::Gather 做局部转置（free compaction），把槽区 strided 行紧凑为连续候选区，再整行向量排序选择前 k——用向量 Gather 解决 round-2 证伪的 free-compaction 前置。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-t2-gather-vector-select.md
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
      "DataCopyGather/Reg::Gather 索引与掩码尾块处理；全排序 O(N log N) 头寸（case_10 4.40×）"
    ],
    "excluded_conditions": [
      "多 chunk 大轴（chunkCount>1，见 topk-t2-chunked-vector-sort-merge）",
      "int/int8 或 sortLen>256 门控排除"
    ],
    "required_conditions": [
      "T2 Q>1 中轴、sortLen<=256、chunkCount==1",
      "槽映射可表达为 Gather 索引",
      "整行候选可驻留 UB"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "incremental 1.1118x; case_8 10.40x, case_10 4.40x, case_20 15.85x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "1edeab57a57d1b782d2bb96e3feb2b3d6a50a2f95529ec4db8e6e3f3fe6031ce",
      "decision_sha256": "e6634105ec8ceb2ce3f0854bbea61531e2b8215d19e8cdd622be0ca3c7c8c282",
      "operator_class": "sort-select",
      "performance_sha256": "5e96383bcb85b469accb1e09f0f3c048da4eb42a501f9e0f649a303c5ab0bff6",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "c8a1e879ab8094647326ff90979174f28ba2b1fe852f345cacfd3c4e372d5432",
      "verify_sha256": "cb800ccd3b863a4f369e90f486f20a78a97e3bc508c42780abfc5d9b3f27d24a"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "strided-slot-scalar-read",
      "t2-scalar-heap"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "gather-free-compaction-vector-select",
    "reduce_mode": "top-k",
    "structure": [
      "vector-gather-compaction",
      "whole-row-vector-select",
      "t2-mid-axis"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-T2-GATHER-VECTOR-SELECT",
  "implementation_steps": [
    "门控 T2 中轴 ES1",
    "向量 Gather 局部转置槽区为连续行",
    "整行向量排序截取前 k"
  ],
  "intent": "把 round-3 已验证的整行向量排序选择迁移到 T2 Q>1 中轴 case（round-3 后仍占 ~86% 且 AIV Scalar 93-100%）。",
  "mechanism": "向量 Reg::Gather 按槽映射局部转置槽区 → 连续候选行 → 整行向量排序截取前 k；门控 chunkCount==1、sortLen<=256、dtype∈{half,bf16,float}。",
  "name": "T2 向量 Gather free-compaction + 整行向量选择",
  "operator_class": "sort-select",
  "operator_scope": "TopK T2 Q>1 中轴 ES1（sortLen<=256、chunkCount==1）case",
  "principle": "stride==1 是向量化的前提；free compaction 必须用向量引擎（Gather）而非标量紧凑（round-2 证伪），成本才低于收益。",
  "related_anti_patterns": [
    "scalar-compaction-cost-exceeds-stride-gain"
  ],
  "risks": [
    "case_15 incremental 0.9345× 为测量会话漂移而非代码回归（代码路径逐字节不变、门控排除、aiv_vec=0）",
    "全排序而非 RADIX_SELECT 的 case 收益有限"
  ],
  "slug": "topk-t2-gather-vector-select",
  "summary": "对 T2 Q>1 中轴 case 用向量 Reg::Gather 做局部转置（free compaction），把槽区 strided 行紧凑为连续候选区，再整行向量排序选择前 k——用向量 Gather 解决 round-2 证伪的 free-compaction 前置。",
  "verification": {
    "correctness": [
      "verify 20/20 通过"
    ],
    "performance": [
      "case_8 10.40×、case_10 4.40×、case_20 15.85×，incremental 1.1118×，regressed=1（case_15 漂移）"
    ],
    "rollback_signals": [
      "非门控 case 真实回归则回退"
    ]
  }
}
-->

# 性能优化策略：T2 向量 Gather free-compaction + 整行向量选择

单一优化点：对 T2 Q>1 中轴 case 用向量 Reg::Gather 做局部转置（free compaction），把槽区 strided 行紧凑为连续候选区，再整行向量排序选择前 k——用向量 Gather 解决 round-2 证伪的 free-compaction 前置。

## 1. 原理

stride==1 是向量化的前提；free compaction 必须用向量引擎（Gather）而非标量紧凑（round-2 证伪），成本才低于收益。

实现机制：向量 Reg::Gather 按槽映射局部转置槽区 → 连续候选行 → 整行向量排序截取前 k；门控 chunkCount==1、sortLen<=256、dtype∈{half,bf16,float}。

## 2. 性能问题模式

- 优化目标：把 round-3 已验证的整行向量排序选择迁移到 T2 Q>1 中轴 case（round-3 后仍占 ~86% 且 AIV Scalar 93-100%）。
- 适用数据流：TopK T2 Q>1 中轴 ES1（sortLen<=256、chunkCount==1）case
- Feature signature：`{"bottleneck": ["strided-slot-scalar-read", "t2-scalar-heap"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "gather-free-compaction-vector-select", "reduce_mode": "top-k", "structure": ["vector-gather-compaction", "whole-row-vector-select", "t2-mid-axis"]}`

## 3. 正确性红线

- case_15 incremental 0.9345× 为测量会话漂移而非代码回归（代码路径逐字节不变、门控排除、aiv_vec=0）
- 全排序而非 RADIX_SELECT 的 case 收益有限

资源与硬件约束：

- DataCopyGather/Reg::Gather 索引与掩码尾块处理；全排序 O(N log N) 头寸（case_10 4.40×）

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- T2 Q>1 中轴、sortLen<=256、chunkCount==1
- 槽映射可表达为 Gather 索引
- 整行候选可驻留 UB

不适用：

- 多 chunk 大轴（chunkCount>1，见 topk-t2-chunked-vector-sort-merge）
- int/int8 或 sortLen>256 门控排除

## 5. 实施步骤

1. 门控 T2 中轴 ES1
2. 向量 Gather 局部转置槽区为连续行
3. 整行向量排序截取前 k

## 6. LLM 前置问题

- 目标实现是否满足：T2 Q>1 中轴、sortLen<=256、chunkCount==1？
- 目标实现是否满足：槽映射可表达为 Gather 索引？
- 目标实现是否满足：整行候选可驻留 UB？
- 是否命中排除条件：多 chunk 大轴（chunkCount>1，见 topk-t2-chunked-vector-sort-merge）？

## 7. 验收标准

正确性：

- verify 20/20 通过

性能：

- case_8 10.40×、case_10 4.40×、case_20 15.85×，incremental 1.1118×，regressed=1（case_15 漂移）

回滚信号：

- 非门控 case 真实回归则回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-compaction-cost-exceeds-stride-gain

- top_k-20260828_120811-77cf84（round=4, status=accepted, speedup=incremental 1.1118x; case_8 10.40x, case_10 4.40x, case_20 15.85x）
- top_k-20260828_120811-77cf84（round=4, status=accepted）

## 检索卡（短卡）

动作：用Reg::Gather按槽映射将槽区局部转置为连续候选行，再整行向量排序并截取前k。
适用：T2 Q>1中轴、sortLen≤256且单chunk，槽映射可表达为Gather索引，整行候选可驻留UB。
限制：分别核验门控内外代码路径、尾块、索引恢复及排序语义。
范围：selection-sort-top-k的T2中轴ES1路径。
检索词：Reg::Gather，free compaction，stride==1，连续候选行，sortLen≤256，单chunk
机会：T2 Q>1中轴仍以标量维护候选，槽映射可被Gather转换为连续行。
代价：整行全排序的复杂度为O(N log N)。
