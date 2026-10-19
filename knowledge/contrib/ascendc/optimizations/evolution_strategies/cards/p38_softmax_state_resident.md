---
type: Optimization
title: 'P38: Softmax 状态 Buffer 跨 S2 循环常驻'
description: Flash Attention 的 online softmax 需要在 S2 方向多次循环中累积 softmaxMax/Sum/Exp
  三个状态。
tags:
- task.optimization
- topic.attention
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P38_softmax_state_resident.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P38: Softmax 状态 Buffer 跨 S2 循环常驻

## 核心思想
Flash Attention 的 online softmax 需要在 S2 方向多次循环中累积 softmaxMax/Sum/Exp 三个状态。这些 buffer 在 InitBuffers 中一次性分配，通过 loop % preLoadNum 索引实现双缓冲复用。

## 代码骨架

// === 改造后（优化实现）===
```cpp
pipe->InitBuffer(softmaxMaxBuff, SOFTMAX_TMP_BUFFER_SIZE * constInfo.preLoadNum);
pipe->InitBuffer(softmaxExpBuff, SOFTMAX_TMP_BUFFER_SIZE * constInfo.preLoadNum);
pipe->InitBuffer(softmaxSumBuff, SOFTMAX_TMP_BUFFER_SIZE * constInfo.preLoadNum);

uint32_t outIdx = info.loop % (constInfo.preLoadNum);
uint32_t softmaxOutOffset = outIdx * SOFTMAX_TMP_BUFFER_SIZE / sizeof(COMPUTE_T);
SoftmaxFlashV2<...>(mmResUb, softmaxSumUb[softmaxOutOffset],
    softmaxMaxUb[softmaxOutOffset], mmResUb,
    softmaxExpUb[softmaxOutOffset], inSumTensor, inMaxTensor, ...);
```

## 关键修改点

1. 预期收益: 状态 buffer 常驻避免每次 S2 循环重新分配，双缓冲索引支持流水重叠

## 常见陷阱

⚠️ 常驻占用 3×2K×preLoadNum = 12KB UB 空间
⚠️ preLoadNum（双缓冲深度）增大可提升流水重叠率，但线性增加 UB 占用

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|SyncAll\|PipeBarrier\|ExecuteTask\|PRELOAD" op_kernel/*.cpp op_host/*_tiling.cpp
```
