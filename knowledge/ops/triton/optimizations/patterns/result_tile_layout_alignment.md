---
type: Optimization
title: Result Tile Layout Alignment Pattern
description: 让计算结果 tile 的轴序与输出内存布局对齐，避免 store 期转置退化为标量逐元素写入。
tags: [task.optimization, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/result-tile-layout-alignment.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Result Tile Layout Alignment Pattern

## Summary

Align the computed result tile's axis order with the output memory layout to avoid store-time transposes that degrade into scalar element writes on Ascend NPU.

## Use When

A kernel computes a result tile (typically a `tl.dot` or reduction
accumulator) and stores it out, but the tile's axis order is the transpose of
the output's contiguous memory layout — for example the tile is `(N, M)` while
the output is a row-major `(M, N)` tensor. The store address therefore strides
across memory instead of advancing contiguously, and profiling or IR
inspection shows the store degraded into per-element scalar writes. The
pattern applies when the tile's axis order is a free choice of the kernel — as
it is for an accumulator — so you can carry the tile in the output's axis
order from the start (swapping the reduction axis and mask broadcast
directions accordingly) instead of paying a store-time transpose.

## Signals

### Code

- The accumulator has shape `(N, M)` but the output tensor is `(M, N)` contiguously in memory.
- `tl.store` uses pointer expressions that stride across the accumulator's leading dimension in a way that mirrors a transpose.
- Reduction axes, mask broadcasts, and final pointer expressions all orbit around a shape convention that mismatches the output.

## Related Patterns

- [cv-intermediate-tile-orientation](./cv_intermediate_tile_orientation.md): choose the orientation of a Cube-to-Vector intermediate, not the public output store.
- [implicit-transpose-elimination](./implicit_transpose_elimination.md): fix GEMM operand physical layout rather than accumulator versus store shape.

## What To Verify After Applying

- Re-check every reduction axis: changing accumulator shape may require changing the reduction dimension.
- Re-check mask broadcasts: the broadcast direction changes when the leading dimension changes.
- Re-check the final pointer expression: confirm it addresses the output in the correct contiguous order.
- Confirm correctness on tail shapes where partial blocks interact with the new axis ordering.

---

## Detail

### Before (accumulator shape mismatches output layout)

```python
# out is a contiguous (M, N) tensor in memory: stride_m = N, stride_n = 1.
# The accumulator and store tile are organized as (N, M), so the tile's last
# axis (m) advances by stride N in memory — a store-time transpose that can
# degrade to scalar writes.
acc = tl.zeros((BLOCK_N, BLOCK_M), dtype=tl.float32)
# ... compute into acc ...
tl.store(out + offs_n[:, None] * stride_n + offs_m[None, :] * stride_m, acc, mask=...)
```

### After (accumulator matches output layout)

```python
# Same output layout (stride_m = N, stride_n = 1), but the accumulator is
# carried as (M, N): the tile's last axis (n) advances by stride 1 in memory,
# so the store is a straight write along the output's contiguous direction.
acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
# ... compute into acc with adjusted reduction axes ...
tl.store(out + offs_m[:, None] * stride_m + offs_n[None, :] * stride_n, acc, mask=...)
```
