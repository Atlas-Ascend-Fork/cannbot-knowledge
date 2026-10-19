---
type: Optimization
title: 'P43: 反向梯度 4路PingPong 常驻与 Scatter-Add 延迟写回'
description: 反向传播中 dK/dV 梯度累积在 workspace 的 4 路 PingPong buffer 中（selectdKPPPidx %
  4 轮转），延迟到整个 S1 处理完毕后再统一 scatter-add，将 scatter-add 从 O(S2) 次降为 O(S1) 次。
tags:
- task.optimization
- paradigm.elementwise
- topic.compute.normalization
- topic.data_movement.memory_access
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P43_grad_pingpong_deferred_scatter.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P43: 反向梯度 4路PingPong 常驻与 Scatter-Add 延迟写回

## 核心思想
反向传播中 dK/dV 梯度累积在 workspace 的 4 路 PingPong buffer 中（selectdKPPPidx % 4 轮转），延迟到整个 S1 处理完毕后再统一 scatter-add，将 scatter-add 从 O(S2) 次降为 O(S1) 次。

## 代码骨架

// === 改造后（优化实现）===
```cpp
selectedKGmOffset = selectdKPPPidx * selectedKWspOffset;
mmPingPongIdx = 1 - mmPingPongIdx;
selectdKPPPidx = (selectdKPPPidx + 1) % 4;
if (scatterRunInfo.changeS1) {
    CrossCoreWaitFlag<2, PIPE_MTE2>(SCATTER_SYNC_FLAG);
    ScatterAddByS1(vecOp, actual_seq_qlen, actual_seq_kvlen);
}
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll
2. 预期收益: scatter-add 次数从 O(S2) 降为 O(S1)，显著减少 GM 写回开销

## 常见陷阱

⚠️ 4 路 PingPong workspace 占用 = 4 × buffer_size × 核数，HBM 开销显著
⚠️ 跨核同步逻辑复杂，changeS1 条件判断和 ScatterAddByS1 触发时机需要精确控制

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|SyncAll\|SetFlag\|WaitFlag\|PipeBarrier\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
