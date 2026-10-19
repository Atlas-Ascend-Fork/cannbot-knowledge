---
type: Optimization
title: 'P29: 跨核同步（AIC-AIV CrossCore Sync）'
description: 在 AIC（Cube 核）和 AIV（Vector 核）之间传递数据时，通过 CrossCoreSetFlag/CrossCoreWaitFlag
  实现跨核同步。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.attention
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P29_crosscore_aic_aiv_sync.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P29: 跨核同步（AIC-AIV CrossCore Sync）

## 核心思想
在 AIC（Cube 核）和 AIV（Vector 核）之间传递数据时，通过 CrossCoreSetFlag/CrossCoreWaitFlag 实现跨核同步。一个 AIC 对应两个 AIV，需要分别同步。

## 代码骨架

// === 改造后（优化实现）===
```cpp
if constexpr (bufferType == BufferType::L1) {
    if ASCEND_IS_AIC {
        CrossCoreWaitFlag<CROSS_CORE_SYNC_MODE, PIPE_MTE1>(id0_);
        CrossCoreWaitFlag<CROSS_CORE_SYNC_MODE, PIPE_MTE1>(id0_ + AIV0_AIV1_OFFSET);
    } else {
        CrossCoreWaitFlag<CROSS_CORE_SYNC_MODE, PIPE_MTE3>(id1_);
    }
}
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll
2. 预期收益: 实现 AIC/AIV 异构核间精确数据交接，支持 Cube-Vector 融合流水线

## 常见陷阱

⚠️ AIC 对应两个 AIV 需要两次 SetFlag/WaitFlag；跨核事件 ID 空间有限
⚠️ 跨核同步延迟高于核内同步，应尽量减少同步次数（批量数据交接优于逐 tile 交接）

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|SyncAll\|SetFlag\|WaitFlag\|PipeBarrier\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
