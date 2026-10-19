---
type: Optimization
title: 'P41: gamma/scale/offset 常驻 UB'
description: gamma（RmsNorm 权重）、quantization scale/offset 等小张量在整个 kernel 生命周期内只搬入一次，常驻
  UB 供所有 ubLoop 迭代复用。
tags:
- task.optimization
- topic.compute.normalization
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P41_gamma_scale_resident.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P41: gamma/scale/offset 常驻 UB

## 核心思想
gamma（RmsNorm 权重）、quantization scale/offset 等小张量在整个 kernel 生命周期内只搬入一次，常驻 UB 供所有 ubLoop 迭代复用。利用 ReinterpretCast 在同一块 buffer 中先存 half 再原地 Cast 为 fp32。

## 代码骨架

// === 改造后（优化实现）===
```cpp
LocalTensor<float> gammaLocalFp32 = inQueueGamma.AllocTensor<float>();
LocalTensor<KV_DTYPE> gammaLocal = gammaLocalFp32.ReinterpretCast<KV_DTYPE>()[RMS_NORM_LENGTH];
DataCopyPad(gammaLocal, gammaGm, copyParams, padParams);
Cast(gammaLocalFp32, gammaLocal, RoundMode::CAST_NONE, RMS_NORM_LENGTH);
// gammaLocalFp32 在所有 ubLoop 中复用
```

## 关键修改点

1. 预期收益: 小张量只搬运一次，消除重复 DMA 开销

## 常见陷阱

⚠️ 常驻 buffer 占用约 2KB UB 空间
⚠️ ReinterpretCast 原地 Cast 技巧要求 float buffer 后半段空间足够存放 half 数据

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|DataCopy\|CopyIn\|CopyOut\|Fixpipe" op_kernel/*.cpp op_host/*_tiling.cpp
```
