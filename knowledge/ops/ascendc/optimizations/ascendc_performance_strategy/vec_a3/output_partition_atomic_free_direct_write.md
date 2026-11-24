---
type: Optimization
title: 按输出区间（列/段）切分核消除原子写与中间 workspace
description: 将scatter-add多核切分从输入行改为输出列/段，使各核独占输出并取消原子串行化及fp32中间区。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-output-partition-atomic-free-direct-write.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：按输出区间（列/段）切分核消除原子写与中间 workspace

> 单一优化点：scatter-add 类算子把切分维度从输入行改为输出区间（列/段），核间写冲突
> 自然消失——免原子串行化、免 fp32 中间 workspace + castout 双通道，实测轮收益
> 0.84x→1.31x。

## 1. 原理

- 默认按输入行分区：多核写同一输出区域 → 依赖 SetAtomicAdd 串行化；fp16/bf16 还要
  fp32 中间 workspace + castout 双通道（GM 流量 ≈4x|x|）+ ws 清零。
- 按输出区间切分后每核独占连续输出区间，写冲突自然消失，可单次非原子 strided 写出；
  fp16/bf16 路径 fp32 累加后单次 cast，精度与 golden 逐位一致。

## 2. 性能问题模式

- scatter-add 类算子按输入行分区导致多核原子写同一输出区域。
- 两种典型触发 shape：
  - a) 小 N 大 te（te/N≥64，N≤64）：行分区每核行数少、原子写块小碎片化；
  - b) 中 N 大 te 的低精度输出（64<N≤2048，te≥2049，fp16/bf16）：ws+castout 流量主导。

## 3. 正确性红线

- int64 数据排除（A2 int64 向量 Add 硬件静默出错）。
- a) 路径 ns*ct*szAcc ≤ UB（ns≤4095 实测）；b) 路径 N≤2048（rowList/rowSlot 入 UB）。

## 4. 泛化条件

- **适用**：a) 小 N 大 te（te/N≥64，N≤64，ns≤4095 且 ns*ct*szAcc ≤ UB）；b) 中 N 大 te
  低精度输出（te≥2049 数据搬运主导、64<N≤2048）。
- **不适用**：int64 数据（A2 向量 Add 静默出错）；N>64 时 a) 路径行循环变长收益反转
  （实测 N=363 劣化）；te<2049 时 b) 路径 O(N) 段扫描开销占比过高。

## 5. 实施步骤

1. a) 列并行（KernelColScatter）：每核独占连续列区间 [c0,c1)，覆盖全部 ns 段全部 N 行；
   逐列 tile 在 UB 清零 acc[ns][ct]，strided 批量读 data，按 seg[j] 向量 Add 累加
   （8 路标量展开连续发 Add），单次 strided 非原子写 y[s][t:t+ct]。
2. b) 段区间直写（KernelSegDirect）：每核独占段区间 [s0,s1)；一次读全部 seg 建
   rowList/rowSlot；逐列 tile 核内 fp32 累加进 acc[mseg][ct]，单次 cast 后 strided
   非原子写 y。免 ws、免 ws 清零、免 castout kernel。

## 6. LLM 前置问题

- 输出是低精度（fp16/bf16）还是 fp32？是否存在 ws+castout 双通道流量主导？
- shape 是否落在 a)（te/N≥64 且 N≤64）或 b)（te≥2049 且 64<N≤2048）触发区间？
- ns*ct*szAcc（或 rowList/rowSlot）是否能放入 UB？
- 数据是否含 int64（A2 向量 Add 硬件静默出错，需排除）？

## 7. 验收标准

- build + 精度全过；实测证据（910B3, UnsortedSegmentSum level2）：
- a) case11 32.8→6.0us、case14 77.4→12.3us、case20 73.2→8.2us、case13 109→56.6us
  （轮收益 0.84x→1.22x，+45%）
- b) case9 555.5→168.4us、case17 27.1→11.2us、case18 25.8→12.6us
  （轮收益 1.22x→1.31x，+7%）
- 两轮精度均 20/20 全过

## 检索卡（短卡）

动作：将scatter-add多核切分从输入行改为输出列/段，使各核独占输出并取消原子串行化及fp32中间区。
适用：小N大te：te/N≥64、N≤64、ns≤4095，且ns*ct*szAcc≤UB。
限制：排除int64数据；每核累加区须满足ns*ct*szAcc≤UB。
范围：scatter-add的列/段输出区间及全部ns段、N行。
检索词：输出区间切分、SetAtomicAdd、fp32 workspace、castout、KernelColScatter。
机会：按输入行分区时，多核原子写同一输出区域。
