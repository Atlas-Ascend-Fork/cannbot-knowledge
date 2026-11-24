---
type: Optimization
title: tile 级 bitlen probe 两遍法——按收敛度驱动迭代次数
description: 把固定最坏上界迭代改为两遍：先探测块内最大 bitlen，再据此动态迭代
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-tile-bitlen-probe-convergence-driven-iterations.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：tile 级 bitlen probe 两遍法——按收敛度驱动迭代次数

> 单一优化点：数据依赖的迭代型 kernel 不再使用固定最坏上界迭代，而是 pass1 核级 probe 出块内 max 的 bitlen，pass2 用动态上界（如 2*bl+4）迭代，避免全部 lane 陪跑最坏上界。

## 1. 原理

- 数据依赖的迭代型 kernel（gcd/求根/格式化输出等）用固定最坏上界迭代；随机数据实际收敛远快于上界，全部 lane 陪跑。
- **两遍法核级 probe**：pass1 只读输入，向量域累积块内 max（每 tile 几条 Max）；每核一次 Cast(float)+ReduceMax+LocalTensor::GetValue(0)（标量管直读 UB，免 GM 往返）得 bl=bitlen(max)；pass2 用动态上界（本例 2*bl+4）。
- 结果修正循环（如左移还原）同样按 bl 限轮。
- 多字表示（int64 双字）时 hi/lo 分开累积：bl = 32+bitlen(maxHi)（hi≥1）else bitlen(maxLo)。
- 改动量级：架构级（限制：probe 必须核级）。

## 2. 性能问题模式

- 迭代收敛型整型算子，瓶颈为 scalar_heavy（固定迭代浪费）：数据实际收敛远快于静态最坏上界，固定上界使全部 lane 陪跑。

## 3. 正确性红线

- 动态上界必须对"该块最坏 lane"成立——上界公式要配套算法变体重新推导（势函数法）。
- **probe 禁止每 tile 做**：GetValue 跨 pipe 同步 ~500us/次，per-tile probe 使 int64 case 反而退化 30%；必须 pass1 向量聚合后每核 1 次。

## 4. 泛化条件

- **适用**：数据依赖的迭代收敛型 kernel（gcd/求根/格式化输出等），实际收敛分布远快于最坏上界。
- **不适用**：迭代次数与数据无关（固定循环）的 kernel；无法廉价聚合出 bitlen 类上界的算法。

## 5. 实施步骤

1. Process 拆两遍。
2. ScanTile：pass1 向量域累积块内 max。
3. ProbeBl：每核 1 次标量读回（Cast+ReduceMax+GetValue(0)）得 bl。
4. pass2 传 bl，按动态上界迭代；结果修正循环同样按 bl 限轮。

## 6. LLM 前置问题

- 迭代次数是否数据依赖，实际收敛是否远快于最坏上界？
- 动态上界公式是否对块内最坏 lane 用势函数法重新推导过？
- probe 是否保证每核仅 1 次（而非每 tile）？
- 多字表示时 hi/lo 的 bitlen 累积是否分开处理？

## 7. 验收标准

- build + 精度全过；gcd：小值域 case 2-13×（P14 13×）；配套 R5 降级后 int64 小值域再 1.3-2.3×。

## 检索卡（短卡）

动作：把固定最坏上界迭代改为两遍：先探测块内最大 bitlen，再据此动态迭代
适用：适合实际收敛远快于最坏上界的数据依赖迭代；固定循环不适用
限制：动态上界须覆盖块内最坏 lane，并针对算法变体重新推导
范围：gcd、求根、格式化输出等数据依赖迭代 kernel
检索词：tile、bitlen probe、两遍法、ReduceMax、GetValue、动态上界、势函数
机会：实际收敛明显早于静态最坏上界，固定迭代使所有 lane 陪跑
