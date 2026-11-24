---
type: Optimization
title: tile 按 UB 预算扩满（下界保护）
description: tile 按 UB 预算扩满（UB/2/2），小 shape 用下界守卫保证每核 >=2 tile 以维持双缓冲重叠。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/tile-fill-ub-budget.md
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
      "按 UB 预算与 buffer liveness 计算，须与实际 buffer 一致"
    ],
    "excluded_conditions": [
      "纯搬移/极小 shape 已由下界守卫覆盖或无深度 2 重叠"
    ],
    "required_conditions": [
      "大 shape 且 UB 有余量；当前 tile 明显小于 UB 预算"
    ]
  },
  "applicability_boundary": "",
  "classification": "lesson",
  "created": "2026-10-12",
  "evidence": [],
  "generality": "op_class",
  "id": "VEC-TILE-FILL-UB-BUDGET",
  "implementation_steps": [
    "按 UB/2/2 估算 tile 上限",
    "对小 shape 施加下界（每核 >=2 tile）",
    "复核 buffer 预算与 liveness 一致",
    "同轮正反序对照验证"
  ],
  "instance_ids": [],
  "intent": "避免固定小 tile 导致搬运事务过多或双缓冲/流水不重叠。",
  "mechanism": "固定 tile（如 4096 元素或 48KB）UB 利用率低、单次搬运事务多、逐 tile 固定开销难摊薄；按 UB 预算扩满可减少事务并提高搬运效率。但小 shape 下若只剩 1 个 loop，深度 2 双缓冲重叠会失效，故须下界保护（每核 >=2 tile）。",
  "name": "tile 按 UB 预算扩满（下界保护）",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "UB 分块搬运类设备代码",
  "principle": "tile 按 UB 预算扩满（UB/2/2 量级），并对小 shape 保下界（每核 >=2 tile 以维持深度 2 重叠）。",
  "provenance": {
    "skill": "由 AOA_vs_BASE 8 算子根因分析（0339/0040/0415）提炼"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "risks": [
    "小 shape 下扩满 tile 可能致重叠失效或 UB 超预算"
  ],
  "schema_version": 2,
  "slug": "tile-fill-ub-budget",
  "source": "skill",
  "status": "seed",
  "summary": "tile 按 UB 预算扩满（UB/2/2），小 shape 用下界守卫保证每核 >=2 tile 以维持双缓冲重叠。",
  "verification": {
    "correctness": [
      "边界 shape（每核 loopTimes=1/2）仍有正确 fallback 且精度通过"
    ],
    "performance": [
      "同轮对照固定小 tile，确认事务/耗时下降且小 shape 无回退"
    ],
    "rollback_signals": [
      "小 shape 出现双缓冲失效或 UB 超预算时回到下界/固定 tile"
    ]
  }
}
-->

# 性能优化策略：tile 按 UB 预算扩满（下界保护）

单一优化点：tile 按 UB 预算扩满（UB/2/2），小 shape 用下界守卫保证每核 >=2 tile 以维持双缓冲重叠。

## 1. 原理

tile 按 UB 预算扩满（UB/2/2 量级），并对小 shape 保下界（每核 >=2 tile 以维持深度 2 重叠）。

固定 tile（如 4096 元素或 48KB）UB 利用率低、单次搬运事务多、逐 tile 固定开销难摊薄；按 UB 预算扩满可减少事务并提高搬运效率。但小 shape 下若只剩 1 个 loop，深度 2 双缓冲重叠会失效，故须下界保护（每核 >=2 tile）。

## 2. 性能问题模式

- 优化目标：避免固定小 tile 导致搬运事务过多或双缓冲/流水不重叠。
- 适用数据流：UB 分块搬运类设备代码
- Feature signature：`{}`

## 3. 正确性红线

- 小 shape 下扩满 tile 可能致重叠失效或 UB 超预算

资源与硬件约束：

- 按 UB 预算与 buffer liveness 计算，须与实际 buffer 一致

## 4. 泛化条件

- 策略作用域：op_class

适用：

- 大 shape 且 UB 有余量；当前 tile 明显小于 UB 预算

不适用：

- 纯搬移/极小 shape 已由下界守卫覆盖或无深度 2 重叠

## 5. 实施步骤

1. 按 UB/2/2 估算 tile 上限
2. 对小 shape 施加下界（每核 >=2 tile）
3. 复核 buffer 预算与 liveness 一致
4. 同轮正反序对照验证

## 6. LLM 前置问题

- 目标实现是否满足：大 shape 且 UB 有余量；当前 tile 明显小于 UB 预算？
- 是否命中排除条件：纯搬移/极小 shape 已由下界守卫覆盖或无深度 2 重叠？

## 7. 验收标准

正确性：

- 边界 shape（每核 loopTimes=1/2）仍有正确 fallback 且精度通过

性能：

- 同轮对照固定小 tile，确认事务/耗时下降且小 shape 无回退

回滚信号：

- 小 shape 出现双缓冲失效或 UB 超预算时回到下界/固定 tile

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：无

- 尚无归档证据（provenance：由 AOA_vs_BASE 8 算子根因分析（0339/0040/0415）提炼）。

## 检索卡（短卡）

动作：tile 按 UB 预算扩满（UB/2/2 量级），小 shape 保下界（每核 >=2 tile 维持双缓冲重叠）
适用：大 shape 且 UB 有余量，固定小 tile 致搬运事务过多或流水不重叠
限制：按 UB 预算与 buffer liveness 计算，须与实际 buffer 一致
范围：跨 operator class 的 UB 分块搬运
检索词：tile、UB 预算、UB/2/2、双缓冲、流水重叠、loopTimes
机会：固定小 tile（4096/48KB）UB 利用率低、单次搬运事务多
代价：需形状自适应推导与下界守卫
