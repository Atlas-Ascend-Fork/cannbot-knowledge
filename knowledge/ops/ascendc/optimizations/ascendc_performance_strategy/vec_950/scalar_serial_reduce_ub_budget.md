---
type: Optimization
title: PIPE_S serial reduce chain + UB-capacity D/K budget
description: Map the scalar serial reduce chain to PIPE_S with a UB-capacity D/K budget, avoiding vector-pipe idling on order-dependent RMW.
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scalar-serial-reduce-ub-budget.md
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
      "PIPE_S must be available"
    ],
    "excluded_conditions": [
      "small cases where RMW not bottleneck"
    ],
    "required_conditions": [
      "scatter reduceMode add/multiply large footprint"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    "runs/scatter-20260828_101109-0c5700/rounds/001/*.json",
    {
      "comparison_sha256": "fec762dccd794798e8a62449a598def8dc87933b9b8c5a514ee67a6cb5b25bdc",
      "decision_sha256": "5c7d8e1c7c237710f73a41d789930c09ae3a333b1b7cd1edef13cbe82e56708e",
      "operator_class": "scatter-update",
      "performance_sha256": "6498379aab4180269bb3a1dba91430c3aeb97e29aad0b9e63d271182b1a4821e",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "77f4ce18ff3debcaabd6c00983845e4e63b56f9cf264d4a806fc723c2b0cdc98",
      "verify_sha256": "922baeff81249485d83e2c9fcfbe9b3ebd719a78faf5279240a776466ec2cf68"
    }
  ],
  "generality": "op_class",
  "id": "SCAT-REDUCE-1",
  "implementation_steps": [
    "scatter_vf.h: move j-order reduce into PIPE_S",
    "scatter_tiling.cpp: UB-budget D/K split"
  ],
  "intent": "Speed up scatter reduce/add large matrices; single-round 4.9x.",
  "mechanism": "j-order reduce chain on PIPE_S; per-chunk D/K budget from UB capacity.",
  "name": "PIPE_S serial reduce chain + UB-capacity D/K budget",
  "operator_class": "scatter-update",
  "operator_scope": "scatter reduce/add large-footprint cases (D/K split j-order RMW chain)",
  "principle": "RMW has a serial dependency; PIPE_S carries it while VEC stays free; split D/K by UB capacity.",
  "risks": [
    "limited on small cases",
    "depends on PIPE_S availability"
  ],
  "slug": "scalar-serial-reduce-ub-budget",
  "summary": "Map the scalar serial reduce chain to PIPE_S with a UB-capacity D/K budget, avoiding vector-pipe idling on order-dependent RMW.",
  "verification": {
    "correctness": [
      "20/20 correctness"
    ],
    "performance": [
      "case 4 5.96x, case 5 6.61x, incremental 4.916x"
    ],
    "rollback_signals": [
      "control regression below 0.95"
    ]
  }
}
-->

# 性能优化策略：PIPE_S serial reduce chain + UB-capacity D/K budget

单一优化点：Map the scalar serial reduce chain to PIPE_S with a UB-capacity D/K budget, avoiding vector-pipe idling on order-dependent RMW.

## 1. 原理

RMW has a serial dependency; PIPE_S carries it while VEC stays free; split D/K by UB capacity.

实现机制：j-order reduce chain on PIPE_S; per-chunk D/K budget from UB capacity.

## 2. 性能问题模式

- 优化目标：Speed up scatter reduce/add large matrices; single-round 4.9x.
- 适用数据流：scatter reduce/add large-footprint cases (D/K split j-order RMW chain)
- Feature signature：`{}`

## 3. 正确性红线

- limited on small cases
- depends on PIPE_S availability

资源与硬件约束：

- PIPE_S must be available

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- scatter reduceMode add/multiply large footprint

不适用：

- small cases where RMW not bottleneck

## 5. 实施步骤

1. scatter_vf.h: move j-order reduce into PIPE_S
2. scatter_tiling.cpp: UB-budget D/K split

## 6. LLM 前置问题

- 目标实现是否满足：scatter reduceMode add/multiply large footprint？
- 是否命中排除条件：small cases where RMW not bottleneck？

## 7. 验收标准

正确性：

- 20/20 correctness

性能：

- case 4 5.96x, case 5 6.61x, incremental 4.916x

回滚信号：

- control regression below 0.95

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- runs/scatter-20260828_101109-0c5700/rounds/001/*.json
- scatter-20260828_101109-0c5700（round=1, status=accepted）

## 检索卡（短卡）

动作：将j序RMW归约链移入PIPE_S以释放VEC，并按UB容量为各块切分D/K预算。
适用：scatter的add或multiply归约，且工作集较大。
限制：必须具备PIPE_S。
范围：scatter-reduce的kernel归约链与host D/K切分。
检索词：PIPE_S串行归约链、UB容量、D/K预算、j序RMW。
机会：大工作集路径存在D/K切分的j序RMW串行链。
代价：小规模中RMW非瓶颈，适用性受限。
