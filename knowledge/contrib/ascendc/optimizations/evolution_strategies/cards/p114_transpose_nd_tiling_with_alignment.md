---
type: Optimization
title: 'P114: Transpose 多维对齐 Tiling 设计'
description: small-channel transpose 类算子先把问题统一建模为 `[C, N] → [N, C]`，其中 `C ≤ 16` 为小通道维，`N`
  为展平长轴。
tags:
- task.optimization
- topic.data_movement.layout_transform
- topic.data_movement.memory_access
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P114_transpose_nd_tiling_with_alignment.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P114: Transpose 多维对齐 Tiling 设计

## 核心思想

small-channel transpose 类算子先把问题统一建模为 `[C, N] → [N, C]`，其中 `C ≤ 16` 为小通道维，`N` 为展平长轴。通过 `TransDataTo5HD` + `vnchwconv` + `Gather` 完成重排，并按 32 元素对齐 `tileNA`，同时满足 `repeats ≤ 255` 与 UB 预算约束。

## 代码骨架

```cpp
// UB 预算与 tile 尺寸
uint32_t ubBudget = ubSize - reservedBytes;
uint32_t perElemBytes = 16 * C + 32;
uint32_t tileNMax = AlignDown(ubBudget / perElemBytes, 32);
tileNMax = Min(tileNMax, 255 * 16);

uint32_t tileN = AlignUp(CeilDiv(N, blockDim), 32);
if (tileN > tileNMax) { /* 重算 tileN 使总 tile 数接近 blockDim 整数倍 */ }

uint32_t tileNA = AlignUp(tileN, 32);
uint32_t repeats = tileNA / 16;
```

## 关键修改点

1. **统一建模**：把任意 small-channel transpose 整理为 `[C, N] → [N, C]`。
2. **对齐规则**：`tileNA = AlignUp(tileN, 32)`；`repeats = tileNA / 16 ≤ 255`。
3. **UB 预算**：`ubBytes = tileNA * (16 * C + 32)`，含双缓冲、中间 buffer、vnchwconv 输出、offset table。
4. **offset table**：按 `tileNA` 构建，每个 16-half block 前 `C` 个位置有效。
5. **多核切分**：`blockDim = min(coreNum, totalTiles)`，`tilesPerCore = ceil(totalTiles / blockDim)`。

## 常见陷阱

- ❌ 把小 C 轴与长轴展平顺序搞反 → layout 错误。
- ❌ `repeats` 超过 255 → 编译失败。
- ❌ offset table 按 `tileN` 而非 `tileNA` 构建 → 越界或 Gather 错位。
- ❌ 尾块未用 `curN` 区分有效长度 → 写入越界。

## 代码搜索关键词

```bash
grep -nE "TransDataTo5HD|vnchwconv|Gather|tileNA|repeats|offsetBuff|SetValue" op_kernel/*.cpp op_host/*_tiling.cpp
```
