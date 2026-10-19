---
type: Optimization
title: 'P42: workspace buffer 多区域分时复用'
description: 一块大的 TBuf<VECCALC> 被划分为多个逻辑区域，供 RmsNorm 和 RoPE 交替使用。
tags:
- task.optimization
- topic.compute.composite
- topic.memory
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p85_on_chip_buffer_zone_reuse
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P42_workspace_zone_reuse.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- a2
---

# P42: workspace buffer 多区域分时复用

> ⚠️ **已废弃**：代码骨架与 P85 逐字重复，且 P85 的描述更通用、更准确。**去向**：[P85: On-Chip Buffer Zone Reuse](p85_on_chip_buffer_zone_reuse.md)。


## 核心思想
一块大的 TBuf<VECCALC> 被划分为多个逻辑区域，供 RmsNorm 和 RoPE 交替使用。RmsNorm 使用 zone0/1/2，RoPE 复用 zone1/2 做 cos/sin 和中间变量。

## 代码骨架

// === 改造后（优化实现）===
```cpp
int64_t xLocalFp32Offset = 0;                  // zone0: RmsNorm fp32
int64_t xSquareLocalOffset = rows * headSize;   // zone1: RmsNorm square / RoPE cos
int64_t xSumLocalOffset = rows * headSize * 2;  // zone2: RmsNorm sum / RoPE sin
LocalTensor<float> xLocalFp32 = wsLocal[xLocalFp32Offset];
LocalTensor<float> xSquareLocal = wsLocal[xSquareLocalOffset];
```

## 关键修改点

1. 预期收益: 一块 buffer 服务多个计算阶段，最大化 UB 利用率

## 常见陷阱

⚠️ 各阶段不能同时执行，zone 复用要求严格的阶段串行顺序
⚠️ wsBuffer 大小 = zone 数 × rows × headSize × sizeof(float)，headSize 较大时占用显著

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue" op_kernel/*.cpp op_host/*_tiling.cpp
```
