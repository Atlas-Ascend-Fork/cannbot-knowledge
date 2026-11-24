---
type: Optimization
title: 减法移位合并与迭代上界同轮收紧（halve-merge + tighten-bound 配套）
description: 将 odd-odd 分支的减法与后续 halve 合为 u'=|u-v|>>1，并在同轮收紧迭代上界。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-halve-merge-tighten-bound-together.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：减法移位合并与迭代上界同轮收紧（halve-merge + tighten-bound 配套）

> 单一优化点：二进制 gcd（Stein）odd-odd 分支的减法与必然发生的 halve 合并为一步（u'=|u-v|>>1），并且**同轮**用势函数收紧迭代上界（4*bl → 2*bl+4）；只合并不收紧上界是零收益。

## 1. 原理

- 二进制 gcd（Stein）odd-odd 分支 (max-min, |u-v|)：|u-v| 必偶，下一迭代必 halve——减法与移位可合并为一步。
- odd-odd 分支取 u'=|u-v|>>1（双字需跨字 HalveLo+hi>>1），v'=min。
- **同轮收紧迭代上界**：该变体下势函数 Φ=bitlen(u)+bitlen(v) 每迭代严格 -1 ⇒ 上界从 4*bl 收紧到 2*bl+4。
- 改动量级：进阶（限制：算法变体与上界必须同轮配套）。

## 2. 性能问题模式

- 迭代收敛型算子，瓶颈为计算体积（迭代次数）：odd-odd 分支减法后必然 halve 却分两步执行，且迭代上界仍按旧算法变体的静态公式（不跟踪实际收敛）。

## 3. 正确性红线

（两条历史教训）
- 只做移位合并不收紧上界 = **零收益**（上界是静态公式，不跟踪实际收敛）。
- 收紧上界必须对**全部路径**补齐对应算法变体：只改单字不改双字时，随机测试因平均收敛短而侥幸通过，对抗 fuzz（Fibonacci 链/幂对/大素数 ±）才能暴露。

## 4. 泛化条件

- **适用**：迭代收敛型算法中"操作合并后势函数下降更快"的变体，可推导出更紧迭代上界。
- **不适用**：合并操作不改变每轮势函数下降量的场景（无上界可收紧，合并收益有限）。

## 5. 实施步骤

1. odd-odd 分支合并：u'=|u-v|>>1（双字需跨字 HalveLo+hi>>1），v'=min。
2. 同轮推导并收紧迭代上界（势函数 Φ=bitlen(u)+bitlen(v) 每迭代严格 -1 ⇒ 2*bl+4）。
3. 对全部路径（单字与双字）补齐对应算法变体。
4. 随机 + 对抗 fuzz（Fibonacci 链/幂对/大素数 ±）回归。

## 6. LLM 前置问题

- 合并后的算法变体是否重新推导了势函数与迭代上界？
- 上界收紧是否覆盖全部路径（含双字/int64 路径）？
- 回归是否包含对抗 fuzz（Fibonacci 链/幂对/大素数 ±）？

## 7. 验收标准

- build + 精度全过；gcd：geo 1.371→1.410（合并+收紧）→1.862（双字补齐），P4 达 525×。

## 检索卡（短卡）

动作：将 odd-odd 分支的减法与后续 halve 合为 u'=|u-v|>>1，并在同轮收紧迭代上界。
适用：适用于操作合并后势函数下降更快、可推导更紧上界的迭代收敛算法。
限制：双字移位必须跨字处理；移位合并与迭代上界收紧必须同轮实施。
范围：二进制 gcd（Stein）的 odd-odd 迭代分支。
检索词：Stein gcd、odd-odd、减法移位合并、势函数、HalveLo、迭代上界
机会：odd-odd 的减法与必然 halve 仍分两步，且循环上界仍用旧静态公式。
代价：若合并不增加每轮势函数下降量，则无法收紧上界，收益有限。
