---
type: Optimization
title: Discrete Memory Access Staging Pattern
description: 先把连续区间整体搬入 UB，再用片上索引选取目标值，替代经离散索引直接读全局内存；固定通道 AoS 可转 SoA 连续读。
tags: [task.optimization, topic.data_movement.memory_access, topic.memory]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/discrete-access-ub-staging.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Discrete Memory Access Staging Pattern

## Summary

Stage a contiguous range into the Unified Buffer first, then use on-chip indexing (`tl.gather` or equivalent) to select target values, rather than loading directly from global memory through discrete indices. For fixed-channel AoS layouts, apply the same principle with channel-first SoA buffers to enable contiguous loads.

## Use When

The kernel's central bottleneck is discrete memory access that semantically
looks like `out = x[idx]`: index-driven global loads dominate the hot path,
and the gather source array is small or medium enough that staging a
contiguous range into the on-chip buffer and selecting locally is more
plausible than direct scattered reads.

A second form: the hot loop reads fixed fields from interleaved records, e.g.
coordinates stored as `[N, 3]` in memory order `x0 y0 z0 x1 y1 z1 ...`, so
reading one field means stride-3 access. The input is reused enough that a
one-time transpose to channel-first order (`x0 x1 ... y0 y1 ...`) on the
wrapper side pays for itself.

## Avoid When

- The source range is too large to stage or transpose profitably for the active shape.
- Memory access patterns are already sequential and contiguous.
- The fixed field dimension is consumed as a whole and splitting it would require vector extraction.
- The rewrite would introduce unsupported Ascend tensor indexing such as `vec[0]` on a loaded vector/tile.

## Signals

### Code

- Channel-wise loads use stride-2/3/4 addressing in the hot vector path.
- Attempts to coalesce fixed fields would require extracting scalar components from a vector.
- A small fixed set of indexed setup values is used only for scalar frame/basis initialization.

### Profile

- Direct discrete global-memory reads appear as the dominant cost in the hot path.
- MTE bandwidth utilization is low relative to the amount of data consumed, indicating poor coalescing.

## Related Patterns

- [live-length-tiling](./live_length_tiling.md): Choose tile widths from the live logical extent on each axis instead of a legacy maximum or blanket power-of-two rule, so masked lanes do not dominate loop trip counts, transfer work, or vector-path work.
- [scattered-transfer-batching](./scattered_transfer_batching.md): When the kernel performs scatter/gather operations with non-contiguous memory access patterns, such as token rearrangement in MOE layers, sparse data processing, or any operation involving index-based data movement, use `extract_slice` or `insert_slice` to data reuse while minimizing expensive global memory transactions.
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [现有知识：离散访存优化（gather_out_to_ub 接口）](../operator_optimization/discrete_memory_access.md)

## What To Verify After Applying

- Verify the source array size is still reasonable for shared memory after the rewrite.
- Verify the kernel stages the source array contiguously before the indexed selection step.
- Verify boundary masking and semantic equivalence with the original gather behavior.

---

## Method

Confirm the fit first: profiling shows discrete, index-driven global reads
dominating the hot path, and the source range is small enough to fit the
on-chip buffer (UB).

The optimization core: never read global memory through discrete indices on
the hot path — move a contiguous range into UB with one wide transfer, then
select on-chip. Two forms:

### Rule: Stage-then-gather for `out = x[idx]`

```python
# Before: scattered global loads, one per lane
val = tl.load(x_ptr + idx * stride_x, mask=mask)

# After: one contiguous transfer into UB, then on-chip indexing
x_ub = tl.load(x_ptr + tl.arange(0, M) * stride_x)
val = tl.gather(x_ub, safe_idx, 0)   # safe_idx: out-of-range lanes clamped, masked at store
```

### Rule: Transpose interleaved records to channel-first when reused

Fixed-field stride-C access (e.g. coordinates stored as `[N, 3]`, read as
`atom_idx * 3 + channel`) cannot be staged profitably per program; transpose
once on the wrapper side, then each channel loads contiguously:

```python
# wrapper, once: [N, 3] -> [3, N]
coordinate_soa = coordinate.t().contiguous()

# kernel: contiguous per-channel loads
x0 = tl.load(coord0_ptr + atom_idx, mask=mask)   # coord0_ptr = base
x1 = tl.load(coord1_ptr + atom_idx, mask=mask)   # coord1_ptr = base + N
x2 = tl.load(coord2_ptr + atom_idx, mask=mask)   # coord2_ptr = base + 2*N
```

Guardrail: keep tiny indexed setup loads scalar. Ascend Triton lowering does
not reliably support vector extraction such as `vec[0]` to split a loaded
vector/tile — do not pack three scalar values into a vector only to extract
the components again.
