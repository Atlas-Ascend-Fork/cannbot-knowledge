---
type: Optimization
title: 'A4: SetFlag/WaitFlag Event Sync (事件同步保证精度)'
description: 参考实现在关键计算节点插入了PipeBarrier<PIPE_V>()进行向量管道同步，确保数据转换和计算操作的正确顺序。
tags:
- task.optimization
- topic.attention
- paradigm.elementwise
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/A4_pipeline_barrier.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# A4: SetFlag/WaitFlag Event Sync (事件同步保证精度)

## 核心思想
参考实现在关键计算节点插入了PipeBarrier<PIPE_V>()进行向量管道同步，确保数据转换和计算操作的正确顺序。这种细粒度的同步控制在BF16的Cast-Compute-Cast流程中尤为重要，防止了数据竞争和乱序执行导致的精度问题。PipeBarrier确保前一步操作完全完成后才执行下一步，虽然会引入一定的性能开销，但对于精度敏感的场景是必要的。参考实现完全没有使用pipeline barrier，在复杂场景下可能出现同步问题。

## 代码骨架

// === 改造后（优化实现）===
```cpp
PipeBarrier<PIPE_V>();
Cast(float32Tensor, dataLocal[index * maxCastDataCount], RoundMode::CAST_NONE, dataCount);
PipeBarrier<PIPE_V>();
op(float32Tensor[offset], float32Tensor, scalarVal, dataCount);
PipeBarrier<PIPE_V>();
Cast(outLocal[index * maxCastDataCount], float32Tensor[offset], RoundMode::CAST_RINT, dataCount);
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll
2. 预期收益: 确保计算顺序正确性，防止数据竞争，保证数值精度

## 常见陷阱

⚠️ 引入同步开销，可能降低流水线效率
⚠️ 增加了同步开销，但精度收益显著
⚠️ 同步会引入轻微性能损失，但对于正确性是必需的

## 代码搜索关键词

```bash
grep -n "SyncAll\|PipeBarrier\|ExecuteTask\|PRELOAD\|SyncAll\|SetFlag\|WaitFlag\|PipeBarrier" op_kernel/*.cpp op_host/*_tiling.cpp
```
