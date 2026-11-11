---
type: Optimization
title: "X16: 循环算子 H-slice 多核切分 (Recurrent H-Slice Multi-Core Split)"
description: "对 LSTM/GRU/RNN/scan 类含串行循环的算子，时间维不可并行，并行度只能从 batch×hidden 中榨取；小 batch 时将 hidden 维度切分到多个 AIV 核，各核独占隐藏单元及对应门控列，递归权重切片 UB 常驻，c/h 状态分片独立更新，零核间通信。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X16: 循环算子 H-slice 多核切分 (Recurrent H-Slice Multi-Core Split)

## 核心思路
对 LSTM/GRU/RNN/scan 类含串行循环的算子，时间维不可并行，并行度只能从 batch×hidden 中榨取。
当 batch 小（核空闲）时，将 hidden 维度切分到多个 AIV 核：每核独占一段隐藏单元
[hStart, hEnd) 及对应的 4 个门控列，W_hh 切片 [hSlice, 4·hSlice] 每核只加载一次并跨
batch tile 与全部时间步复用（UB 常驻），c/h 状态切片各核独立更新，**零核间通信**
（循环依赖 h_t→h_{t+1} 的完整 h 通过每核各算全量 h 的递归投影后各自取片，或 x_proj
已由 host GEMM 提供时内核只剩小 GEMV）。host 侧 tiling 按 shape 在 batch-parallel 与
H-slice 两种模式间调度（经验阈值：batchNum≤4 或 (H≥256 且 batchNum≤32) 走 H-slice）。

## 适用场景
- 含时间步串行依赖的算子（LSTM/GRU/RNN/线性 scan）
- 小 batch（核占用率低）或中大 H（单核算力/UB 成为瓶颈）的 shape
- 与 X15 组合：X15 把非递归投影外提走 Cube 后，内核只剩递归残差，H-slice 解决
  残差部分在小 batch 下的多核利用——两者正交，组合收益叠乘

## 实现要点
- **门控列映射（关键正确性约束，必须遵守）**：4H 融合门控维布局为 [i|f|g|o] 四个 H 块，
  隐藏单元 j 的四个门控列是 {j, H+j, 2H+j, 3H+j}，**不是**连续的 [4j, 4j+4)。
  W_hh/W_ih/bias 切片必须按跨步列取，按连续 [4·hStart, 4·hEnd) 切会导致 i/f/g/o
  张冠李戴——该 bug 表现为精度随机挂（输入分布温和时碰巧通过）、c 状态超数学上界
  甚至 fp16 Inf。x_proj 若由 host 按 gate-major [seq,4,batch,H] 排布则天然正确
- host 侧 tiling 调度两种模式，所有 shape 统一走 kernel，不要保留 host 回退循环
  （回退路径会掩盖未优化的 shape）
- H-slice 缓冲区全部 ALIGN32 对齐；调度阈值需按目标平台校准
- 每核 W_hh 切片 UB 常驻后，剩余 UB 决定 batch tile 大小，二者需一起算预算

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
