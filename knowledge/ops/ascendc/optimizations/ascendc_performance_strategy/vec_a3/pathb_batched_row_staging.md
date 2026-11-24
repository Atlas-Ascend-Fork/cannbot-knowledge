---
type: Optimization
title: Path B 批量行中转（一次 DataCopyPad 搬多行消除 MTE2 短突发）
description: 将inner>1的2D归约从逐行DataCopyPad改为每次批量搬运redTile行。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-pathb-batched-row-staging.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Path B 批量行中转（一次 DataCopyPad 搬多行消除 MTE2 短突发）

> 单一优化点：(inner>1) 的 2D 归约不再逐行 DataCopyPad，改为每次搬 redTile 行，消除每行一次 MTE2 + 队列同步的短突发低效。

## 1. 原理

- (inner>1) 的 2D 归约逐行 DataCopyPad：每行一次 MTE2 + 队列同步，行长小（如 404B×1024 行）时 MTE2 短突发效率极低。
- 每次 2D DataCopyPad 搬 redTile 行（redTile = clamp(UB 预算/行宽, 1, 64)，双缓冲时预算减半），`dstGap=0` 依赖 DataCopyPad 的自动 32B 对齐行距（dummy padding），搬完在 UB 内按 rowStride=align32(blockLen)/esz 走行处理。行长可任意（不需 32 对齐）。
- 与 05-pathb-double-buffer 叠加使用。
- 改动量级：进阶策略。

## 2. 性能问题模式

- (inner>1) 的 2D 归约逐行 DataCopyPad：每行一次 MTE2 + 队列同步，行长小（如 404B×1024 行）时 MTE2 短突发效率极低。

## 3. 正确性红线

- `dstGap=0` 依赖 DataCopyPad 的自动 32B 对齐行距（dummy padding），UB 内走行必须按 rowStride=align32(blockLen)/esz，不可按原始行长。
- 行长可任意（不需 32 对齐），但 redTile 的 UB 预算核算不可省（双缓冲时预算减半）。

## 4. 泛化条件

- **适用**：(inner>1) 的 2D 归约、行长较小的逐行搬运场景；对降级路径的 Path B 同样生效。
- **不适用**：行长已足够大、单次 MTE2 即可吃满带宽的场景。

## 5. 实施步骤

1. 计算 redTile = clamp(UB 预算/行宽, 1, 64)（双缓冲时预算减半）。
2. 每次 2D DataCopyPad 搬 redTile 行，`dstGap=0`，依赖自动 32B 对齐行距（dummy padding）。
3. 搬完在 UB 内按 rowStride=align32(blockLen)/esz 走行处理。

## 6. LLM 前置问题

- 当前是否逐行 DataCopyPad 且行长小导致 MTE2 短突发？
- redTile 是否按 UB 预算 clamp 到 [1,64]，双缓冲时是否预算减半？
- UB 内走行的 rowStride 是否按 align32(blockLen)/esz 计算？

## 7. 验收标准

- build + 精度全过；geo 0.5458→0.5774；P20 615→222us（2.8x）；对降级路径的 Path B 同样生效（P08 300→171us）。

## 检索卡（短卡）

动作：将inner>1的2D归约从逐行DataCopyPad改为每次批量搬运redTile行。
适用：适用于inner>1、行长较小且逐行搬运的2D归约，包括降级Path B。
限制：redTile按UB预算和行宽钳制到1至64；双缓冲预算减半；dstGap=0依赖自动32B对齐行距。
范围：inner>1的2D归约及降级Path B。
检索词：2D DataCopyPad、redTile、MTE2、dstGap、32B对齐、UB预算。
机会：小行长下每行一次MTE2并伴随队列同步，形成大量短突发。
代价：行长足够大且单次MTE2已能吃满带宽时不适用。
