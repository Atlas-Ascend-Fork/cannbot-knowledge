---
type: Optimization
title: 'A1: FP32 Intermediate Computation (FP32中间计算)'
description: 参考实现在DAG中显式地进行了类型转换：输入数据类型U (BF16/FP16) 被转换为T (FP32) 后进行所有计算，最后转换回U输出。
tags:
- task.optimization
- paradigm.elementwise
- topic.mixture_of_experts
- topic.compute.normalization
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/A1_fp32_intermediate.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# A1: FP32 Intermediate Computation (FP32中间计算)

## 核心思想
参考实现在DAG中显式地进行了类型转换：输入数据类型U (BF16/FP16) 被转换为T (FP32) 后进行所有计算，最后转换回U输出。这种设计确保了累加精度（AdaGrad中accum的累加操作在FP32上进行，避免BF16/FP16的精度损失）、除法精度（sqrt(accum)和除法操作在FP32上进行，减少数值误差）、梯度精度（梯度平方和乘法在更高精度下进行）。参考实现全程使用float32，虽然精度足够但失去了BF16/FP16的内存带宽优势。

## 代码骨架

// === 改造前（基线）===
```cpp
// 参考实现仅FP32，无需转换
AscendC::Add(accumLocal, accumLocal, inputLocal, C);
```

// === 改造后（优化实现）===
```cpp
// 升精度累加
if constexpr (std::is_same_v<T, float>) {
    Add(sumBufLocal, sumBufLocal, inputLocal, len);
} else {
    LocalTensor<float> castBufLocal = castBuf.Get<float>();
    Cast(castBufLocal, inputLocal, RoundMode::CAST_NONE, len);
    Add(sumBufLocal, sumBufLocal, castBufLocal, len);
}

// 降精度输出
Cast(outputLocal, sumBufLocal, RoundMode::CAST_RINT, len);
```

## 关键修改点

1. 预期收益: 有效避免FP16/BF16多次累加产生的精度损失，数值稳定性提升

## 常见陷阱

⚠️ 需要额外的castBuf和sumBuf(FP32)存储空间
⚠️ 需要在Tiling阶段计算每个输出点的kernel大小
⚠️ 增加了类型转换操作的开销，但通常远小于内存带宽节省的收益

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
