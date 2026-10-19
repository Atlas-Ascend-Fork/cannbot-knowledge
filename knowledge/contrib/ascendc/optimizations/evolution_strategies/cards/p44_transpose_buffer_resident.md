---
type: Optimization
title: 'P44: Transpose Buffer 常驻复用'
description: gradTransposeBuf_ 作为转置后的梯度数据常驻 UB，在整个 numIters 迭代循环中被 colNormGrad/rowNormGrad
  反复原地读写，只在首尾各做一次转置和 GM 搬运。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.attention
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P44_transpose_buffer_resident.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P44: Transpose Buffer 常驻复用

## 核心思想
gradTransposeBuf_ 作为转置后的梯度数据常驻 UB，在整个 numIters 迭代循环中被 colNormGrad/rowNormGrad 反复原地读写，只在首尾各做一次转置和 GM 搬运。

## 代码骨架

// === 改造后（优化实现）===
```cpp
TBuf<TPosition::VECCALC> gradTransposeBuf_;
void Process() {
    TransposeXIn();
    for (int j = numIters_ - 1; j > 0; --j) {
        colNormGrad();
        rowNormGrad();
    }
    TransposeXOut();
    CopyOut(offset);
}
```

## 关键修改点

1. 预期收益: 迭代过程中零 DMA 开销，所有计算在片上完成

## 常见陷阱

⚠️ 占用 tAlign_×n_×n_×4 字节，n 较大时成为 tiling 瓶颈
⚠️ TransposeXIn/Out 本身有开销，仅在迭代次数较多（≥3）时收益明显

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|DataCopy" op_kernel/*.cpp op_host/*_tiling.cpp
```
