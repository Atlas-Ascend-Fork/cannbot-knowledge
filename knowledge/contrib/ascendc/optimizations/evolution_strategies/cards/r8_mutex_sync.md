---
type: Optimization
title: 'R8: Mutex 细粒度同步'
description: 使用 Mutex 替代粗粒度 SetFlag/WaitFlag，减少流水线停顿。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R8_mutex_sync.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R8: Mutex 细粒度同步

> ⚠️ **已废弃**：使用虚构 Mutex::Lock API，与 P28/P29/P30 同步策略重叠，零引用，仅作方向留档。**去向**：无直接继任卡，仅留档参考。


## 核心思想
使用 Mutex 替代粗粒度 SetFlag/WaitFlag，减少流水线停顿。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// Baseline: 粗粒度同步（等待整个流水完成）
SetFlag<HardEvent::MTE2_V>(eventId);
WaitFlag<HardEvent::MTE2_V>(eventId);
// 所有 MTE2 操作都完成后才继续

// Evolved: Mutex 细粒度同步
Mutex::Lock(PIPE_MTE2);
// 仅锁定 MTE2 流水
DataCopy(ubTensor, gmTensor, count);
Mutex::Unlock(PIPE_MTE2);
// MTE2 解锁后其他流水可继续
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll

## 常见陷阱

⚠️ 收益**: 减少不必要的流水线等待
⚠️ 风险**: 过细粒度的同步增加编程复杂度
⚠️ 复杂度**: 高

## 代码搜索关键词

```bash
grep -n "GetBlockNum\|coreNum\|blockIdx\|SplitCore\|DataCopy\|CopyIn\|CopyOut\|Fixpipe" op_kernel/*.cpp op_host/*_tiling.cpp
```
