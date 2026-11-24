---
type: Optimization
title: scatter-add 类算子的核内局部归约
description: 把逐行GM原子写改为整chunk搬入UB，并在accLocal[ns]中做标量RMW局部累加。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.atomic
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-onchip-partial-reduction-for-scatter-add.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：scatter-add 类算子的核内局部归约

> 单一优化点：te==1（每行单元素）的 scatter-add 类算子把逐行 GM 原子写（次数 = N，可达
> 百万级）替换为核内 UB 局部累加器 + 结尾按块原子写回，原子次数从 N 降到每核
> ceil(ns/1024)，实测最高 99x。

## 1. 原理

- 每一行（或每个 1 元素行）逐次通过 `SetAtomicAdd + DataCopyPad` 原子写到 GM 目标段，
  MTE3 原子事务次数 = N；te==1 的 1D case 每行 1 元素 = 一次 4B 原子事务，ns==1 全归约
  时退化为一根百万次原子累加到 y[0] 的标量依赖链。
- 核内局部归约：批量 MTE2 把 seg 与 data 整 chunk 搬入 UB，在 UB 局部累加器
  accLocal[ns] 上做标量 RMW 累加，结尾 `SetAtomicAdd` 把 accLocal 按 1024 元素块原子
  写回——原子次数从 N 降到每核 ceil(ns/1024)。

## 2. 性能问题模式

- 算子本质是 scatter-add（segment-sum / index-add / scatter-add 类），输出段数 ns 与
  输入行数 N 独立。
- profiling 特征：MTE3 原子事务次数 = N（可达百万级），主 kernel 耗时与 N 成正比而与
  数据量不成比例。
- te==1 的 1D case 尤其严重（每行 1 元素 = 一次 4B 原子事务）；ns==1 全归约退化为百万次
  原子累加的标量依赖链。

## 3. 正确性红线

- ACC 类型须支持硬件原子（fp32/int32）。
- accLocal[ns] 必须能完整放入 UB（fp32 时 ns ≲ 40k），否则越界。

## 4. 泛化条件

- **适用**：te==1（每行单元素）的 scatter-add；ACC 类型支持硬件原子（fp32/int32）；
  acc[ns] 可入 UB；chunk 大小由 UB 预算钳制（seg + data + cast 缓冲 + acc），设下限防
  chunk 过小开销反转。
- **不适用**：ACC 类型不支持硬件原子；ns 超出 UB 容量的场景。

## 5. 实施步骤

1. 批量 MTE2 把 seg 与 data 整 chunk 搬入 UB（消除逐行 1 元素小请求）。
2. 在 UB 局部累加器 accLocal[ns] 上做标量 RMW 累加（4 路展开 + "4 个 seg 互异时先并行读
   再写"快路径打散编译器保守串行链）。
3. 结尾 `SetAtomicAdd` 把 accLocal 按 1024 元素块原子写回——原子次数从 N 降到每核
   ceil(ns/1024)。
4. ns==1 全归约特例：用向量 `ReduceSum` 整 chunk 归约替代标量累加链。

## 6. LLM 前置问题

- 输入是否 te==1（每行单元素）的 1D/2D 形态？
- ACC dtype 是否支持硬件原子（fp32/int32）？ns 是否小到 acc[ns] 可入 UB？
- chunk 大小是否在 UB 预算（seg + data + cast 缓冲 + acc）内且有下限防开销反转？
- 是否存在 ns==1 全归约 case（应走向量 ReduceSum 特例）？

## 7. 验收标准

- build + 精度全过；实测证据（910B3, UnsortedSegmentSum level2）：
- case15 (N≈1.05M 1D fp32, ns=1)：1168.6us → 11.8us（99x）
- case12 (N≈1.05M 1D fp16, ns=1024)：6134.8us → 356.1us（17x）
- case16 (N≈2.1M 1D fp16, ns=4096)：4167.2us → 705.1us（5.9x）
- 精度 20/20 全过；整轮（含其他迁移点）0.40x → 0.84x

## 检索卡（短卡）

动作：把逐行GM原子写改为整chunk搬入UB，并在accLocal[ns]中做标量RMW局部累加。
适用：te==1的单元素行scatter-add，ACC支持fp32/int32硬件原子，且acc[ns]可放入UB。
限制：ACC须支持fp32/int32硬件原子；accLocal[ns]须完整放入UB。
范围：te==1的单元素行scatter-add路径。
检索词：scatter-add、segment-sum、index-add、SetAtomicAdd、DataCopyPad、accLocal。
机会：每个单元素行都以SetAtomicAdd和DataCopyPad写GM，原子事务数随N增长。
