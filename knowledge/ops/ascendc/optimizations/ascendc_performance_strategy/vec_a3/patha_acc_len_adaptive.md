---
type: Optimization
title: Path A 累加器长度自适应（accLen 随实际归约长度取 2 的幂）
description: 将固定大累加器及整段归约长度改为不小于min(red,TILE)的最小2次幂。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-patha-acc-len-adaptive.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Path A 累加器长度自适应（accLen 随实际归约长度取 2 的幂）

> 单一优化点：向量归约 kernel 的累加器/整段归约长度不再硬编码固定大值，而是按实际归约长度取不小于它的最小 2 的幂。

## 1. 原理

- 向量归约 kernel 的累加器/整段归约长度硬编码为固定大值（如 8192），实际归约长度 red 更小时计算量放大固定值/red 倍（本案例 4~22x）。
- accLen = 2^ceil(log2(min(red, TILE)))（host 算好入 tiling）；Duplicate/ReduceXxx/tile 循环统一用 accLen。2 的幂保证树归约语义不变；尾段 tile 只搬有效长度（DataCopyPad 支持任意 blockLen），pad 区保持 initVal（sum=0 / max=-inf / min=+inf）不污染结果。
- 改动量级：基础策略（几十行，零风险）。

## 2. 性能问题模式

- 向量归约 kernel 的累加器/整段归约长度硬编码为固定大值（如 8192），实际归约长度 red 更小时计算量放大固定值/red 倍（本案例 4~22x）。

## 3. 正确性红线

- accLen 必须取 2 的幂（2^ceil(log2(min(red, TILE)))），保证树归约语义不变。
- 尾段 tile 只搬有效长度，pad 区必须保持 initVal（sum=0 / max=-inf / min=+inf），不得污染归约结果。

## 4. 泛化条件

- **适用**：实际归约长度常小于硬编码累加器长度的向量归约 kernel；归约类型为 sum/max/min 等 initVal 明确的归约。
- **不适用**：red 恒大于等于固定值、无放大倍数的场景（无收益）。

## 5. 实施步骤

1. host 侧计算 accLen = 2^ceil(log2(min(red, TILE)))，写入 tiling。
2. kernel 内 Duplicate/ReduceXxx/tile 循环统一改用 accLen。
3. 尾段 tile 用 DataCopyPad 只搬有效长度，pad 区保持 initVal。

## 6. LLM 前置问题

- 当前累加器长度是否硬编码为固定大值而实际归约长度更小？
- accLen 是否保持 2 的幂以维持树归约语义？
- 尾段 pad 区的 initVal 是否与归约类型（sum/max/min）匹配？

## 7. 验收标准

- build + 精度全过；geo 0.5094→0.5458；P09 2046→1379us（-33%）、P10 51.8→29.5us（0.60→1.02x）。

## 检索卡（短卡）

动作：将固定大累加器及整段归约长度改为不小于min(red,TILE)的最小2次幂。
适用：实际red常小于硬编码长度，且为sum/max/min等initVal明确的向量归约。
限制：accLen必须为2^ceil(log2(min(red,TILE)))，以保持树归约语义。
范围：sum、max、min等向量归约kernel。
检索词：accLen、red、TILE、2次幂、Duplicate、ReduceXxx、tile循环。
机会：实际red小于固定累加长度，计算量被放大为固定值/red倍。
代价：red恒大于等于固定值时不适用。
