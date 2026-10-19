---
type: Optimization
title: Shift Mask-Reduce to Load
description: 把 2D mask-and-reduce 构造的 shift/前驱路径改写为 base + arange - 1 的一维索引流直读。
tags: [task.optimization, topic.compute.indexing, topic.implementation.masking]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/shift-mask-reduce-to-load.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Shift Mask-Reduce to Load

## Summary

When a hot shift or predecessor path is expressed as a 2D mask-and-reduce construction, rewrite it to a direct 1D index stream (`base + arange - 1`) with only boundary masking. This removes unnecessary 2D intermediates and keeps the shift path closer to one-dimensional vector loads and elementwise math on Ascend NPU; do not stop at replacing the reduce with an on-chip `tl.gather` if the final lane formula can be simplified further.

## Use When

The kernel shifts every lane one position (`out[i] = x[i-1]`), with lane 0
handled specially. The code builds this shift with a 2D mask-and-reduce
instead of a direct shifted load:

```python
shift_mask = offs_i == (offs_j + 1)
shifted = tl.sum(tl.where(shift_mask, x[None, :], 0.0), axis=1)
```

The mask-reduce builds an N×N boolean matrix to fetch each element's left
neighbor — O(N²) work for what is one shifted load.

IR shows `tt.broadcast` / `tt.reduce` work that serves only the shift path,
and profiling shows overhead concentrated there.

A 1D predecessor load replaces the quadratic mask-and-reduce with one
shifted load.

## Avoid When

- The dependency is not a simple predecessor relation and truly needs multi-source gather semantics.
- Boundary behavior depends on nonlocal logic that cannot be encoded as a simple masked predecessor load.
- The path is not hot enough for rewrite complexity to be worthwhile.
- The shifted intermediate is reused by multiple later expressions and direct predecessor reloads would add more traffic than the 2D form removes.
- The proposed rewrite only changes `tl.sum(tl.where(mask, ...))` into `tl.gather` over a previously computed shifted intermediate while preserving the same extra global loads and intermediate computation. That is usually an incomplete rewrite, not the intended pattern.

## Signals

### Code

- Shift path computes with 2D masks and reduction-like reconstruction.
- Lane 0 receives special handling via separate path while other lanes follow "previous lane" semantics.
- The same shift can be expressed with:
  - `idx = chunk_start + tl.arange(0, BLOCK) - 1`
  - `mask = idx >= 0`
  - masked 1D loads from source tensors.
- The square mask is fixed by lane coordinates rather than by data-dependent values.

## Method

Confirm the pattern applies: the hot path is a pure predecessor shift, the 2D mask is fixed by lane coordinates rather than data-dependent values, and the shift path is measurable in the profile.

The optimization core is to derive the final per-output-lane formula first, then express the shift as a 1D index stream `idx = base + tl.arange(0, BLOCK) - 1` with a single boundary mask `idx >= 0`. Load only the operands that truly come from the predecessor lane; destination-local operands stay at the current lane. After the rewrite compiles, delete the obsolete next-lane loads, shifted intermediates, and any `tl.gather` lane-reorder left over from the old form.

### Rule: Replace the 2D mask-reduce with a 1D predecessor load

Build predecessor indices as a 1D vector and keep one boundary mask for invalid positions:

```python
# Before: 2D mask/reduce shift assembly
shift_mask = offs_i == (offs_j + 1)
shifted = tl.sum(tl.where(shift_mask, x[None, :], 0.0), axis=1)

# After: direct 1D predecessor stream
idx = chunk_start + tl.arange(0, BLOCK) - 1
valid = idx >= 0
shifted = tl.load(x_ptr + idx * stride, mask=valid, other=0.0)
```

### Rule: Compose the shift into the final lane formula

If the 2D path first computes `values[j]` from inputs at `j + 1` and then shifts `values[j]` to output `j + 1`, simplify the composition before loading. Often only the upstream gradient or source value is shifted, while destination-local operands remain at the current lane:

```python
# values[j] = current_operand[j + 1] * upstream[j]
# shifted[i] = values[i - 1] = current_operand[i] * upstream[i - 1]
idx = chunk_start + tl.arange(0, BLOCK) - 1
prev_upstream = tl.load(upstream_ptr + idx * stride, mask=idx >= 0, other=0.0)
shifted = current_operand * prev_upstream
```

### Rule: Do not stop at tl.gather over a shifted intermediate

Replacing the reduce with `tl.gather` over a fully computed shifted intermediate keeps the same extra loads and intermediates; that is an incomplete rewrite:

```python
# Incomplete: removes the reduce but keeps the shifted intermediate.
next_operand = tl.load(ptr + (offs + 1) * stride, mask=(offs + 1) < n, other=0.0)
values = next_operand * upstream
shifted = tl.gather(values, tl.maximum(tl.arange(0, BLOCK) - 1, 0), 0)

# Preferred: shift only the operand the final lane formula needs.
prev_upstream = tl.load(
    upstream_ptr + (offs - 1) * stride,
    mask=offs > 0,
    other=0.0,
)
shifted = current_operand * prev_upstream
```

## What To Verify After Applying

- Exact correctness on lane-0 and cross-chunk boundaries.
- Equality against reference for both full chunks and edge chunks.
- IR no longer shows the targeted `tt.broadcast` / `tt.reduce` or the 2D shift-mask construction path.
- End-to-end benchmark improves on representative shapes, not only micro-cases.
- The rewrite did not blindly shift destination-local operands that should remain at the current lane.
- The generated code no longer keeps unnecessary `next` loads, shifted temporary vectors, or `tl.gather` just to emulate the old mask-reduce result.

## Related Patterns

- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md): Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md): Split exact-tile hot paths from generic masked kernels when dispatch-time shape guards can prove there are no tail tiles, so Ascend lowering can avoid boundary-only masks, padding values, block-pointer `boundary_check`, and related control branches.
- [algebraic-optimization](./algebraic_optimization.md): Apply mathematical identities and semantics-preserving rewrites to reduce redundant memory passes, full data scans, or live ranges before micro-tuning loads.
- [intermediate-layout-copy-deletion](./intermediate_layout_copy_deletion.md): Avoid materializing tensors whose only purpose is to change logical layout, such as `permute`, `transpose`, `movedim`, `reshape`, `squeeze`, or `unsqueeze`, when the next step immediately copies, stores, reduces, gathers, or otherwise consumes the data.
