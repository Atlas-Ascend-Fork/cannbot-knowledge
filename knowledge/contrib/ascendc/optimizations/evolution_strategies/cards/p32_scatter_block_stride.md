---
type: Optimization
title: 'P32: Scatter Block Update 的 stride 寻址'
description: 支持输入张量 dim-0 非连续（通过 inputStride0_ 和 inputStride1_），实现 input[indices[k,0],
  indices[k,1], :] = update[k, :] 的散射写入。
tags:
- task.optimization
- topic.compute.indexing
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P32_scatter_block_stride.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P32: Scatter Block Update 的 stride 寻址

## 核心思想
支持输入张量 dim-0 非连续（通过 inputStride0_ 和 inputStride1_），实现 input[indices[k,0], indices[k,1], :] = update[k, :] 的散射写入。

## 代码骨架

// === 改造后（优化实现）===
```cpp
for (int64_t i = 0; i < loadCount; i++) {
    IndexT idx0 = indLocal.GetValue(i * INDICES_LAST_DIM);
    IndexT idx1 = indLocal.GetValue(i * INDICES_LAST_DIM + 1);
    int64_t gmOffset = static_cast<int64_t>(idx0) * inputStride0_
                     + static_cast<int64_t>(idx1) * inputStride1_;
    DataCopyExtParams copyParams;
    copyParams.blockCount = 1;
    copyParams.blockLen = updateDimSize_ * sizeof(T);
    DataCopyPad(inputGm_[gmOffset], updLocal[i * updateRowElements_], copyParams);
}
```

## 关键修改点

1. 预期收益: 支持非连续张量的散射更新，无需预先 reshape

## 常见陷阱

⚠️ 逐行写出每次只搬 1 行 MTE3 效率低
⚠️ indices 需要先搬入 UB 解析，增加额外的 MTE2 搬运和标量计算开销

## 代码搜索关键词

```bash
grep -n "DataCopy\|CopyIn\|CopyOut\|Fixpipe" op_kernel/*.cpp op_host/*_tiling.cpp
```
