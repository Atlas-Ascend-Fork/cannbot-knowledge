---
type: Optimization
title: Path B 输入队列双缓冲（MTE2 与 Vector 计算重叠）
description: 将输入TQue从bufferNum=1改为2，使MTE2搬运与Vector计算重叠。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-pathb-double-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Path B 输入队列双缓冲（MTE2 与 Vector 计算重叠）

> 单一优化点：TQue 单缓冲（bufferNum=1）导致 MTE2 搬运与 Vector 计算完全串行，输入队列改 bufferNum=2 实现搬运与计算重叠。

## 1. 原理

- TQue 单缓冲（bufferNum=1）导致 MTE2 搬运与 Vector 计算完全串行。
- 输入队列 bufferNum=2；行预算按每 buffer 减半。开双缓冲前先核 UB 预算：(bufferNum×buffer + 全部计算缓冲) ≤ UB。
- 改动量级：基础策略。

## 2. 性能问题模式

- TQue 单缓冲（bufferNum=1）导致 MTE2 搬运与 Vector 计算完全串行。

## 3. 正确性红线

- 开双缓冲前必须核 UB 预算：(bufferNum×buffer + 全部计算缓冲) ≤ UB。Path A 类"计算缓冲多且等长"形态 fp32 恰好 192KB 溢出（2×32KB in + 4×32KB calc），需同步缩 tile，否则 507035。

## 4. 泛化条件

- **适用**：输入队列单缓冲导致搬运与计算串行的场景；UB 预算充裕（核算后不溢出）的 kernel。
- **不适用**：UB 预算核算后溢出且无法同步缩 tile 的形态（如 Path A 类"计算缓冲多且等长"的 fp32 形态 192KB 溢出）。

## 5. 实施步骤

1. 输入队列 bufferNum 改为 2。
2. 行预算按每 buffer 减半。
3. 开双缓冲前先核 UB 预算：(bufferNum×buffer + 全部计算缓冲) ≤ UB，溢出时同步缩 tile。

## 6. LLM 前置问题

- 当前输入队列是否 bufferNum=1 导致 MTE2 与 Vector 完全串行？
- (bufferNum×buffer + 全部计算缓冲) 核算后是否 ≤ UB，是否存在 192KB 溢出形态？
- 行预算是否按每 buffer 减半？

## 7. 验收标准

- build + 精度全过；geo 0.5774→0.6066（仅 Path B 生效）；无 507035（UB 溢出）错误。

## 检索卡（短卡）

动作：将输入TQue从bufferNum=1改为2，使MTE2搬运与Vector计算重叠。
适用：输入队列单缓冲使搬运与计算串行，且核算后UB预算不溢出。
限制：必须满足bufferNum×buffer加全部计算缓冲不超过UB。
范围：Path B的输入队列。
检索词：TQue、bufferNum、双缓冲、MTE2、Vector计算、UB预算。
机会：TQue为单缓冲，MTE2搬运与Vector计算完全串行。
代价：每个buffer的行预算减半；UB溢出且无法缩tile时不适用。
