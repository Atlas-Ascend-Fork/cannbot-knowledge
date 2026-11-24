---
type: Optimization
title: 行归一化与后继列统计的 pass 融合
description: 在生成行归一化结果时同步累加列统计量，删除一次矩阵重读与屏障。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/fused-row-column-statistics-pass.md
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
      "融合后的列统计累加顺序和累加 dtype 必须满足原算法精度契约",
      "每行归一化结果在被覆盖前必须完成其对列统计量的贡献"
    ],
    "excluded_conditions": [
      "第二统计量依赖完整的后续阶段结果、需要不同的数据顺序，或融合会显著增加 UB 压力时不适用",
      "单独统计 pass 已被其他计算完全隐藏，或矩阵过大导致融合寄存器溢出时收益有限"
    ],
    "required_conditions": [
      "迭代算法在同一轮内先生成逐行归一化值，随后再次扫描这些值计算列统计量",
      "列统计量可在生成每行归一化结果时增量累加",
      "统计量规模能够常驻 UB 或寄存器"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 829.98,
      "before_us": 2360.97,
      "case": "20-case-sum",
      "operator_class": "vv-fusion",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821.md",
      "speedup": 2.84,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "redundant-pass",
      "local-memory-barrier"
    ],
    "dtypes": [
      "fp32"
    ],
    "pattern": "fused-row-column-statistics",
    "reduce_mode": "iterative-normalization",
    "structure": [
      "pass-fusion",
      "row-normalize",
      "column-reduce"
    ]
  },
  "gain": "20 用例耗时和 2360.97→829.98us，2.84x；单用例约 1.29–5.44x。",
  "generality": "op_class",
  "id": "NORM-SINKHORN-FUSED-STATS",
  "implementation_steps": [
    "画出每轮 row normalize、column statistics 和后续 normalize 的数据依赖",
    "在片上初始化列统计累加器，并在生成每行归一化结果时立刻累加对应列",
    "删除独立的列统计重读 pass，只保留统计量对下一阶段可见所需的一次同步",
    "核对融合前后累加顺序、低精度提升和迭代边界，非适用 shape 回退原路径",
    "用不同 batch、矩阵尺寸和迭代次数验证全量精度及累计收益"
  ],
  "intent": "消除迭代归一化中生成行归一化结果后又为列统计量完整重读一次的冗余 pass。",
  "mechanism": "在 pass1 计算每行归一化值的同时，把该行对 colSum 等后继统计量的贡献累加到常驻片上缓冲；后续阶段直接消费该统计量，从三次 UB 扫描降为两次，并减少一次 LocalMemBar。",
  "name": "行归一化与后继列统计的 pass 融合",
  "op": "mhc_sinkhorn",
  "operator_class": "vv-fusion",
  "operator_scope": "每轮交替执行行归一化和列统计/归一化、且中间矩阵可按行流式消费的迭代归一化数据流",
  "principle": "后继列统计是已生成行归一化值的线性聚合时，无需为它再次扫描整矩阵；在生产数据的同一 pass 中增量累加，可同时减少片上流量和同步。",
  "provenance": {
    "final_summary": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821/final_summary.json",
    "source_report": "<PERF_ROOT>/strategies/mhc_sinkhorn_opt_20260821.md"
  },
  "related_anti_patterns": [
    "per-row-pipebarrier-sync"
  ],
  "risks": [
    "融合改变浮点求和顺序，迭代次数多时微小误差可能累积",
    "统计量生命周期延长会增加寄存器或 UB 压力并可能引发 spill"
  ],
  "schema_version": 2,
  "slug": "fused-row-column-statistics-pass",
  "source": "external_verified",
  "status": "applied",
  "summary": "在生成行归一化结果时同步累加列统计量，删除一次矩阵重读与屏障。",
  "verification": {
    "correctness": [
      "覆盖不同矩阵尺寸、batch、迭代次数与极端值，逐轮比较统计量并执行全量精度验证"
    ],
    "performance": [
      "确认 UB 扫描由三次降为两次、LocalMemBar 减少，并测量不同迭代次数下的收益"
    ],
    "rollback_signals": [
      "迭代误差累积超限、寄存器 spill、UB 超限或小矩阵启动开销回归时回退"
    ]
  }
}
-->

# 性能优化策略：行归一化与后继列统计的 pass 融合

单一优化点：在生成行归一化结果时同步累加列统计量，删除一次矩阵重读与屏障。

## 1. 原理

后继列统计是已生成行归一化值的线性聚合时，无需为它再次扫描整矩阵；在生产数据的同一 pass 中增量累加，可同时减少片上流量和同步。

实现机制：在 pass1 计算每行归一化值的同时，把该行对 colSum 等后继统计量的贡献累加到常驻片上缓冲；后续阶段直接消费该统计量，从三次 UB 扫描降为两次，并减少一次 LocalMemBar。

## 2. 性能问题模式

- 优化目标：消除迭代归一化中生成行归一化结果后又为列统计量完整重读一次的冗余 pass。
- 适用数据流：每轮交替执行行归一化和列统计/归一化、且中间矩阵可按行流式消费的迭代归一化数据流
- Feature signature：`{"bottleneck": ["redundant-pass", "local-memory-barrier"], "dtypes": ["fp32"], "pattern": "fused-row-column-statistics", "reduce_mode": "iterative-normalization", "structure": ["pass-fusion", "row-normalize", "column-reduce"]}`

## 3. 正确性红线

- 融合改变浮点求和顺序，迭代次数多时微小误差可能累积
- 统计量生命周期延长会增加寄存器或 UB 压力并可能引发 spill

资源与硬件约束：

- 融合后的列统计累加顺序和累加 dtype 必须满足原算法精度契约
- 每行归一化结果在被覆盖前必须完成其对列统计量的贡献

## 4. 泛化条件

- 策略作用域：op_class：vv-fusion

适用：

- 迭代算法在同一轮内先生成逐行归一化值，随后再次扫描这些值计算列统计量
- 列统计量可在生成每行归一化结果时增量累加
- 统计量规模能够常驻 UB 或寄存器

不适用：

- 第二统计量依赖完整的后续阶段结果、需要不同的数据顺序，或融合会显著增加 UB 压力时不适用
- 单独统计 pass 已被其他计算完全隐藏，或矩阵过大导致融合寄存器溢出时收益有限

## 5. 实施步骤

1. 画出每轮 row normalize、column statistics 和后续 normalize 的数据依赖
2. 在片上初始化列统计累加器，并在生成每行归一化结果时立刻累加对应列
3. 删除独立的列统计重读 pass，只保留统计量对下一阶段可见所需的一次同步
4. 核对融合前后累加顺序、低精度提升和迭代边界，非适用 shape 回退原路径
5. 用不同 batch、矩阵尺寸和迭代次数验证全量精度及累计收益

## 6. LLM 前置问题

- 目标实现是否满足：迭代算法在同一轮内先生成逐行归一化值，随后再次扫描这些值计算列统计量？
- 目标实现是否满足：列统计量可在生成每行归一化结果时增量累加？
- 目标实现是否满足：统计量规模能够常驻 UB 或寄存器？
- 是否命中排除条件：第二统计量依赖完整的后续阶段结果、需要不同的数据顺序，或融合会显著增加 UB 压力时不适用？

## 7. 验收标准

正确性：

- 覆盖不同矩阵尺寸、batch、迭代次数与极端值，逐轮比较统计量并执行全量精度验证

性能：

- 确认 UB 扫描由三次降为两次、LocalMemBar 减少，并测量不同迭代次数下的收益

回滚信号：

- 迭代误差累积超限、寄存器 spill、UB 超限或小矩阵启动开销回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-pipebarrier-sync

- strategy-mhc-sinkhorn-20260821-s1（status=accepted, case=20-case-sum, speedup=2.84）

## 检索卡（短卡）

动作：把后继列统计从独立重扫改为在生成每行归一化值的同一 pass 中增量累加。
适用：同轮先生成逐行归一化值、再扫描求列统计，且列统计可逐行增量累加。
限制：列统计累加顺序和dtype须满足原精度契约；行归一化结果须在覆盖前完成相关列统计消费。
范围：normalization 中每轮的行归一化与列统计路径。
检索词：row normalize、column statistics、colSum、线性聚合、pass 融合。
机会：行归一化结果生成后仍被完整重读一次以计算列统计量。
代价：会改变浮点求和顺序；统计量生命周期延长会增加寄存器或 UB 压力。
