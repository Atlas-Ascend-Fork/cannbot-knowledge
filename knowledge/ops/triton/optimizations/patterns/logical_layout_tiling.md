---
type: Optimization
title: Logical-Layout Tiling Pattern
description: 当逻辑操作是仿射数据搬运时，用布局感知的多维 tile 取代标量密集的 1D 线性索引遍历。
tags: [task.optimization, topic.tiling, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/logical-layout-tiling.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Logical-Layout Tiling Pattern

## Summary

Replace scalar-heavy 1D linear-index traversal with layout-aware multidimensional tiles when the logical operation is an affine data movement.

The anti-pattern is a kernel that walks `numel(out)` as a flat stream, then reconstructs logical coordinates with `//` and `%` for every lane before computing source or destination offsets. For regular layout operations, this turns simple memory movement into repeated scalar index decoding. The repair is to make the Triton tile axes match the logical output layout: rows, columns, and rank axes are represented directly by `tl.arange` tensors, so pointer offsets are mostly base-plus-stride arithmetic over contiguous or low-stride dimensions.

This is broader than permute. It applies to transpose/permute copies, reshape copies, pad/crop/slice copies, bounded affine gathers, and other copy-like kernels where the mapping from output coordinates to input coordinates is static and affine.

## Use When

The kernel is mostly affine data movement — a copy, transpose, reshape, pad,
crop, or slice — not dense arithmetic or a reduction. It is launched over a
flat `n_elements` or `out.numel()` range, and each lane rebuilds its logical
coordinates with division and remainder chains before computing load or store
offsets:

```python
offs = pid * BLOCK + tl.arange(0, BLOCK)
c0 = offs // s0
r0 = offs % s0
c1 = r0 // s1
```

The output-to-input mapping is affine: coordinates map through strides, axis
reorder, fixed offsets, or padding bounds, with no data-dependent
indirection. At least one logical dimension is contiguous or low-stride, so
it can become a tile axis. Profiling shows high scalar and control overhead
for what should be a cheap copy.

Tiling to the logical layout removes the per-lane div/mod decoding, leaving
base-plus-stride addressing.

## Avoid When

- Indices are value-dependent or irregular enough that the hot path is true gather/scatter; use gather/discrete-access patterns instead.
- The layout rewrite can be removed entirely by folding the layout into the next consumer.
- The operation is compute-heavy enough that index decode is not a meaningful bottleneck.
- Rank/stride/shape assumptions are not guarded and would silently change semantics.
- A multidimensional tile would exceed UB/register budget or create invalid grid dimensions.

## Signals

### Code

- `offsets = pid * BLOCK + tl.arange(...)` is the main work assignment.
- The kernel computes `coord0 = linear // stride0`, `residual = linear % stride0`, then repeats for more axes.
- A single flattened mask combines all rank or boundary conditions for every lane.
- Inner dimensions are looped or decoded even though they could be represented as tile axes.
- The same generic kernel handles simple cases such as identity copy, 2D transpose, last-dim slice, or regular pad.

### Profile

- Changing only flat `BLOCK_SIZE` gives weak or unstable gains.
- Cases with more rank dimensions or larger flattened sizes regress disproportionately.
- Specialized row-column or multidimensional tile variants improve regular shape regimes.

## Method

Confirm the fit first: the profile shows high scalar/control overhead and the
code shows division/remainder coordinate chains, so removing decode work —
not moving fewer bytes — is what should change latency. Record the flat-tile
baseline before rewriting.

The optimization core is to make the tile axes match the logical output
layout, so offsets become base-plus-stride arithmetic over contiguous or
low-stride dimensions, then add guarded fast paths for simpler layouts and
keep tiles within the UB budget. Apply one rule at a time and keep only
changes that beat the recorded baseline.

### Rule: Promote the effective contiguous dimension into the tile

Pick a logical inner dimension that gives contiguous or low-stride access on either load or store. Often this is the last non-unit output dimension, not necessarily the physical last axis.

```python
rows = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
cols = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
mask = (rows[:, None] < num_rows) & (cols[None, :] < inner_size)

src = row_src_base[:, None] + cols[None, :] * src_inner_stride
dst = row_dst_base[:, None] + cols[None, :] * dst_inner_stride
vals = tl.load(x + src, mask=mask, other=0.0)
tl.store(out + dst, vals, mask=mask)
```

This changes coordinate work from per-element div/mod to per-row base setup plus vector stride increments.

### Rule: Use rank-aware tile axes instead of residual decode chains

For small fixed ranks, express each active coordinate as a tensor axis and compute offsets directly:

```python
d0 = d0_start + tl.arange(0, BLOCK_D0)[:, None, None, None]
d1 = d1_start + tl.arange(0, BLOCK_D1)[None, :, None, None]
d2 = d2_start + tl.arange(0, BLOCK_D2)[None, None, :, None]
d3 = d3_start + tl.arange(0, BLOCK_D3)[None, None, None, :]

src = d0 * src_s0 + d1 * src_s1 + d2 * src_s2 + d3 * src_s3
dst = d0 * dst_s0 + d1 * dst_s1 + d2 * dst_s2 + d3 * dst_s3
```

This is useful for generic rank-limited layout copies where a row-column collapse would hide important stride differences.

### Rule: Add guarded simple-case fast paths

Before launching the generic path, split out cases with much simpler layout:

- identity or contiguous copy,
- 2D transpose,
- last-two-axis swap that can be reshaped into a 2D transpose,
- pure slice/crop with contiguous inner spans,
- pad regimes where interior columns need no input-boundary checks.

Fast paths must be guarded by shape, permutation, and stride checks, and benchmarked against the generic fallback.

### Rule: Choose tile sizes from stride locality and UB footprint

Prefer widening dimensions with stride `1` or small stride first. Bound the total tile product by dtype, live tensors, masks, and temporary values. A useful heuristic is to grow one axis at a time while the UB estimate stays below budget, then choose `num_warps` from the resulting tile size.

### Rule: Cap grid dimensions with grid-stride loops

If the backend or runtime benefits from capped grid dimensions, do not truncate work. Use `tl.num_programs(axis=*)` and loop with a grid stride:

```python
for row_start in tl.range(pid_m * BLOCK_M, rows_total, tl.num_programs(0) * BLOCK_M):
    ...
```

This lets a smaller physical grid cover a large logical tensor.

### Candidate: Row-tiled form when the contiguous length is wider than the tile

For stencil or sliding-window access, try the row-tiled form first when the contiguous length (`W`) is comfortably wider than the tile width. Promote the row into the grid and tile axes: a grid axis decodes `(row, column-tile)`, each tap's address is `scalar_base + kh*row_stride + kw + tl.arange(0, BLOCK)`, and stores are affine with a column-tail mask. Choose the crossover against the flat-segment form by matched measurements, not by a fixed ratio.

### Candidate: Flat-segment form when the contiguous length is narrower than the tile

If the contiguous length is narrower than the tile width, column tiling wastes lanes. Use a flat-segment form instead:

- lanes are contiguous positions in the padded-flat buffer and may span rows;
- each tap load is `scalar_base + constant_shift + tl.arange(0, BLOCK)`, where the constant shift is `(kh-1)*row_stride + (kw-1)` relative to the output pixel's own padded position, **not** `kh*row_stride + kw`;
- compute the row/column decode and border validity once per tile on the store side, and let stores carry the validity mask.

Size the pad and block so the flat form's waste is about `2/row_stride` (pad columns) plus image tail, instead of `(covered - W)/covered`. Mixing the two tap-shift conventions is the classic off-by-one-row bug; only differential tests catch it, not timing.

A separate shifted packing copy (im2col/unfold-style, written to memory before the consumer) is often a symptom of one-dimensional grid thinking: shifted or row-crossing tile accesses force per-lane coordinate reconstruction, so a copy gets introduced to simplify consumer addressing. Before adding such a copy — and again after adding it — try the two-dimensional grid decode above; it can remove the per-lane decode and the extra copy together.

Discipline note: `tl.make_block_ptr` metadata is not a dependable affine-address remedy on this backend's mixed cube/vector lowering — it may compile without producing descriptor-based loads and can add overhead. Prefer explicit two-dimensional grid decode with plain pointer arithmetic unless a descriptor path is verified in the generated code.

## Failure Modes And Anti-signals

- Replacing flat decode with a multidimensional tile but still doing per-lane div/mod inside the tile.
- Choosing the literal last dimension as the inner dimension when it is size `1` or high-stride.
- Adding a fast path without exact guards for rank, shape, stride, dtype, and output contract.
- Ignoring destination layout: contiguous loads with scattered stores can still bottleneck if store shape is poor.
- Grid caps without grid-stride loops cause incomplete writes.
- Over-widened tiles reduce scalar work but increase UB/register pressure enough to regress.

## What To Verify After Applying

- Correctness across full tiles, tails, empty tensors, unit dimensions, and every dispatched rank/shape path.
- Baseline-vs-specialized performance for each fast-path branch and the generic fallback.
- The optimized kernel has fewer or no hot-path `//` / `%` coordinate decode operations.
- Load/store offsets match the true source and destination strides.
- Tile product stays within practical UB/register pressure on largest representative cases.
- Grid caps plus grid-stride loops cover all logical elements exactly once.

## Related Patterns

- `layout-store-and-block-pointers`: Use block pointers when regular tiles lower as fragmented or scalar transfers.
- [pad-copy-row-col-tiling](./pad_copy_row_col_tiling.md): Rewrite flat 1D copy kernels over `numel(out)` into row–column tiled form to reduce scalar overhead from per-element coordinate reconstruction on the last dimension.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): Amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md): Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.
- `gather-load`: Stage contiguous data in UB before applying indirect indexing or gather.
- [discrete-access-ub-staging](./discrete_access_ub_staging.md): Stage a contiguous range into the Unified Buffer first, then use on-chip indexing (`tl.gather` or equivalent) to select target values, rather than loading directly from global memory through discrete indices.
- [simt-window-reduction-tuning](./simt_window_reduction_tuning.md) — outer dispatch and inner-path routing on Ascend 950 SIMT fixed-window reduces: Use for Ascend 950 SIMT fixed-window reductions after enabling SIMT launch mode.
- [simt-window-divisor-formula](./simt_window_divisor_formula.md) — closed normalizer inner window loop after outer tiling: Use closed-form clipped bounds when full-window masked counting is costly.
