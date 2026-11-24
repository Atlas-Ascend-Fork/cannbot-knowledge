---
type: Optimization
title: T2 split UB-window relocation
description: Stage the tile's full idx/upd K-extent once and relocate the UB window, eliminating dNum-fold GM re-staging within an 8192B span.
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/t2-split-ub-window-relocation.md
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
      "8192B UB window span"
    ],
    "excluded_conditions": [
      "small footprint where GM re-staging negligible"
    ],
    "required_conditions": [
      "T2 split update/atomic large footprint"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    "runs/scatter-20260828_101109-0c5700/rounds/004/*.json",
    {
      "comparison_sha256": "2d7e4eb730d9b3d74d8e919783ebb5169fb683b74e2ed0bf7429c79d900ade29",
      "decision_sha256": "42eb64c7a3d999e03c19ab6bdef908959ae6ad22321f60fa7837dd895cbde8ea",
      "operator_class": "scatter-update",
      "performance_sha256": "8272dacd39a85ef77870f45e408c696a0be395bdcf7a0034c9f0fe949ea5e303",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ab0b196035faf3b34d26a7efb8fd77a3ca032ca489f194d842891dbc24c79476",
      "verify_sha256": "517c63d8d2aea5bf76a7ce2a6661cf6559196f664c05b0d3d01617dff37e18f9"
    }
  ],
  "generality": "op_class",
  "id": "SCAT-REDUCE-2",
  "implementation_steps": [
    "scatter_t2.h UB-window relocation",
    "scatter_tiling.cpp span budget"
  ],
  "intent": "Speed up case 6 and similar T2 large footprints (50->23ms).",
  "mechanism": "scatter_t2.h full K-extent staging + sliding UB window.",
  "name": "T2 split UB-window relocation",
  "operator_class": "scatter-update",
  "operator_scope": "T2 split large-footprint update/atomic paths",
  "principle": "one full idx/upd K-extent staging + UB window relocation avoids dNum GM round-trips.",
  "risks": [
    "8192B span constraint"
  ],
  "slug": "t2-split-ub-window-relocation",
  "summary": "Stage the tile's full idx/upd K-extent once and relocate the UB window, eliminating dNum-fold GM re-staging within an 8192B span.",
  "verification": {
    "correctness": [
      "14/14 correctness"
    ],
    "performance": [
      "case 6 2.20x, incremental 1.332x"
    ],
    "rollback_signals": [
      "control regression below 0.95"
    ]
  }
}
-->

# 性能优化策略：T2 split UB-window relocation

单一优化点：Stage the tile's full idx/upd K-extent once and relocate the UB window, eliminating dNum-fold GM re-staging within an 8192B span.

## 1. 原理

one full idx/upd K-extent staging + UB window relocation avoids dNum GM round-trips.

实现机制：scatter_t2.h full K-extent staging + sliding UB window.

## 2. 性能问题模式

- 优化目标：Speed up case 6 and similar T2 large footprints (50->23ms).
- 适用数据流：T2 split large-footprint update/atomic paths
- Feature signature：`{}`

## 3. 正确性红线

- 8192B span constraint

资源与硬件约束：

- 8192B UB window span

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- T2 split update/atomic large footprint

不适用：

- small footprint where GM re-staging negligible

## 5. 实施步骤

1. scatter_t2.h UB-window relocation
2. scatter_tiling.cpp span budget

## 6. LLM 前置问题

- 目标实现是否满足：T2 split update/atomic large footprint？
- 是否命中排除条件：small footprint where GM re-staging negligible？

## 7. 验收标准

正确性：

- 14/14 correctness

性能：

- case 6 2.20x, incremental 1.332x

回滚信号：

- control regression below 0.95

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- runs/scatter-20260828_101109-0c5700/rounds/004/*.json
- scatter-20260828_101109-0c5700（round=4, status=accepted）

## 检索卡（短卡）

动作：将反复 GM staging 改为完整预载 idx/upd 的 K 范围，并滑动重定位 UB 窗口。
适用：T2 split update/atomic 的大工作集路径。
限制：UB 滑动窗口跨度必须满足 8192B 限制。
范围：scatter-reduce 的 scatter_t2.h 更新/原子路径。
检索词：T2 split、full K-extent staging、sliding UB window、GM round-trips。
机会：T2 split update/atomic 大工作集反复从 GM staging。
代价：小工作集若 GM 重暂存可忽略，则不适用。
