---
type: Optimization
title: "X148: 先量 Fixpipe 忙占比，再决定是否优化其它链"
description: "CV 环中 Fixpipe（L0C→GM）有一个与 shape 关系不大的写率；当中间量必须保持 fp32 时，Fixpipe 忙占比会随规模收敛到接近饱和。此时再优化 AIV 链或 MTE1 链通常没有净收益，因为它们在与 FIX 抢同一个墙。判定顺序应是先量 aic_fixpipe_ratio，再决定投入方向。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.architecture
status: draft
sources: []
created_at: "2026-10-28T13:20:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X148: 先量 Fixpipe 忙占比，再决定是否优化其它链

## 核心思路
CV 融合环里 AIC 的 Fixpipe（L0C→GM）有一个不随 shape 明显变化的写率（由行宽、ndNum、密度等决定）。当中间量必须保持 fp32（精度门封死 2 字节方案）时，Fixpipe 忙占比会随规模收敛到接近饱和。此时再优化 AIV 链或 MTE1 链的**净收益往往接近 0**——因为它们与 FIX 抢同一个 wall。

## 适用场景
- A2/910B 上所有"AIC 产中间量 → GM ring → AIV 消费"的融合算子（attention / indexer / topk score）。
- 尤其适用于有人报告"中间量往返带宽墙"的场景——那个数字通常是结果不是约束（见 X146）。

## 实现要点
1. **判定（成本很低）**：用 `msprof --aic-metrics=PipeUtilization` 取 `aic_fixpipe_ratio`。若已接近饱和（显著高于其它 pipe），先判"FIX 型天花板"，不要优先做 AIV/MTE1/字节/task 粒度优化。
2. **五类"看似该有效"的干预，先假设无效**：
   - 把 AIV 归约从多次 Axpy 换成转置布局的 Mul + WholeReduceSum，并同时大幅削减 MTE1 字节；
   - 把中间量写字节砍到 0；
   - task 数翻倍或减半；
   - 每 task 减少若干 SetWaitFlag + PipeBarrier；
   - ring 加深或 mGroup 翻倍（足迹不变）。
   若 FIX 已饱和，这些干预的净收益可能都落在噪声内。先用小探针确认，再决定是否投入完整实现。
3. **唯一还能动的两支**：
   - 把 FIX 写率本身推高（更宽的行、`ndNum>1`、更高密度、减少碎片化写）；
   - 换一个**不需要 FIX 出口**的算法分解。在 A2 上这条路被 X147 封死：L0C→UB 无通路，L0C→L1 只支持量化到不超过 2 字节。
4. **区分"写率饱和"与"单 shape 饱和"**：固定写率不等于所有 shape 都饱和；小 shape 可能受 launch/握手支配，仍应按 X141/X172 分档。

## 验证方法
- msprof PipeUtilization 取 2–3 个代表 shape，确认 `aic_fixpipe_ratio` 与总时长的关系。
- 对每个候选干预做同窗口 A/B；若目标 pipe 比例明显下降而墙钟不变，说明它不在临界路径。
- 若 FIX 未饱和，本卡的"其他链无效"结论不适用，应按常规 roofline 继续分析。

## 关联
- 与 [X146](disc_x146.md)（字节墙三步探针）互补：X146 判断"是不是字节墙"，X148 判断"FIX 是否已经饱和"。
- 与 [X147](disc_x147.md)（L0C 出口限制）共同解释为什么 A2 上很难绕开 FIX。
