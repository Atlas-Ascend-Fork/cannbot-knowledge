---
type: Optimization
title: 'R7: SIMD/SIMT 混合编程'
description: 对同一算子中的不同操作，根据访问模式选择 SIMD 或 SIMT 模型。
tags:
- task.optimization
- topic.compute.composite
status: deprecated
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/R7_simd_simt_hybrid.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- '950'
---

# R7: SIMD/SIMT 混合编程

> ⚠️ **已废弃**：使用虚构 __simt_vf__ / threadIdx.x 等 CUDA 风格 API，AscendC 不存在，零引用，仅作方向留档。**去向**：无直接继任卡，仅留档参考。


## 核心思想
对同一算子中的不同操作，根据访问模式选择 SIMD 或 SIMT 模型。

## 代码骨架

// === 改造后（优化实现）===
```cpp
// SIMT: 不规则 gather
__simt_vf__ __launch_bounds__(1024)
inline void GatherVF(__ubuf__ float* output, __gm__ float* input,
                     __ubuf__ int32_t* indices, int count) {
    for (int idx = threadIdx.x; idx < count; idx += blockDim.x) {
        output[idx] = input[indices[idx]];
    }
}

// SIMD: 规则逐元素计算
__simd_vf__ inline void ComputeVF(__ubuf__ float* dst, __ubuf__ float* src,
    uint32_t count, uint32_t oneRepSize, uint16_t repTimes) {
    RegTensor<float> srcReg, dstReg;
    MaskReg mask;
    for (uint16_t i = 0; i < repTimes; ++i) {
        mask = UpdateMask<float>(count);
        LoadAlign(srcReg, src + i * oneRepSize);
        Adds(dstReg, srcReg, 1.0f, mask);
        StoreAlign(dst + i * oneRepSize, dstReg, mask);
    }
// ... (truncated)
```

## 常见陷阱

⚠️ 收益**: 不规则访问性能提升显著（SIMT 天然支持随机访问）
⚠️ 风险**: SIMD/SIMT 切换有开销，不宜频繁切换
⚠️ 复杂度**: 高（需要同时掌握两种编程模型）

## 代码搜索关键词

```bash
grep -n "GetBlockNum\|coreNum\|blockIdx\|SplitCore\|GatherVF\|ComputeVF" op_kernel/*.cpp op_host/*_tiling.cpp
```
