---
type: Optimization
title: 'P30: PipeBarrier 密集插入的纯 Vector 同步'
description: 在递推类算子（y0→y1→y2 依赖链）中，每条 Vector 指令后插入 PipeBarrier<PIPE_V>，确保前一条指令结果写入
  UB 后才被下一条读取。
tags:
- task.optimization
- paradigm.elementwise
- topic.compute.normalization
- topic.compute.reduction
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P30_dense_pipebarrier_vector.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P30: PipeBarrier 密集插入的纯 Vector 同步

## 核心思想
在递推类算子（y0→y1→y2 依赖链）中，每条 Vector 指令后插入 PipeBarrier<PIPE_V>，确保前一条指令结果写入 UB 后才被下一条读取。

## 代码骨架

// === 改造后（优化实现）===
```cpp
Mul(y2BufLocal, x32BufLocal, weight2, curDim_);
PipeBarrier<PIPE_V>();
Add(y2BufLocal, y1BufLocal, y2BufLocal, curDim_);
PipeBarrier<PIPE_V>();
Mul(y1BufLocal, x32BufLocal, weight1, curDim_);
PipeBarrier<PIPE_V>();
Add(y1BufLocal, y0BufLocal, y1BufLocal, curDim_);
PipeBarrier<PIPE_V>();
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll
2. 预期收益: 保证递推依赖链的正确性，避免乱序执行导致的数据错误

## 常见陷阱

⚠️ 密集 barrier 阻止 Vector 流水线内部的指令级并行
⚠️ 每条 Vector 指令后插入 PipeBarrier 会增加约 1-2 个周期的同步开销
