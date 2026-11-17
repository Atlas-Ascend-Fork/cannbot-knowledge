---
type: Optimization
title: Block Pointer 规则 Tile 表达
description: 将规则多维 tile 的逐元素指针改为块指针，并用 IR 和基准验证传输与寻址收益。
tags:
- task.optimization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/block-pointer-tiles.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Block-Pointer Tiles

## Summary

Use `tl.make_block_ptr` as a compiler-facing representation candidate when source semantics define a regular multidimensional tile but IR suggests that manual pointer expressions lower into unexpectedly scalarized, fragmented, strided, or transpose-heavy memory operations. Treat the rewrite as a heuristic experiment: confirm that it improves emitted transfer shape or address generation, then retain it only when correctness and benchmark evidence support it.

## Use When

Your kernel accesses a logically regular rectangular tile — predictable
offsets, contiguous or regularly strided axes — but expresses it as per-lane
pointer arithmetic, and IR or profiling shows the access lowered into
fragmented, scalarized, or non-coalesced transfers:

```python
rows = m0 + tl.arange(0, BLOCK_M)[:, None]
cols = n0 + tl.arange(0, BLOCK_N)[None, :]
tile = tl.load(x + rows * stride_m + cols * stride_n, mask=...)   # tile load
# or the same arithmetic on the store side:
tl.store(out + rows * stride_m + cols * stride_n, acc, mask=...)
# or a load followed by an explicit transpose for a dot operand:
k_t = tl.trans(tl.load(k_ptrs, mask=k_mask))
```

## Avoid When

- Addresses come from runtime indices, sparse metadata, hash lookups, or other data-dependent gather/scatter semantics that do not form a regular tile.
- IR already shows the expected block-shaped transfer and address generation is not a meaningful cost.
- The measured bottleneck is recurrence work, Cube compute, unavoidable transferred bytes, or synchronization rather than transfer fragmentation.

These are routing signals, not hard prohibitions. A low-cost isolated experiment is still reasonable when source regularity is clear but IR attribution is incomplete.

## Signals

### Code

- Manual pointer arithmetic reconstructs multidimensional coordinates from a flat `program_id`.
- A rectangular tile is expressed as per-element `base + row * stride_row + col * stride_col` addresses and masks.
- A small inner dimension is loaded through an explicit loop even though it could be part of `block_shape`.
- A regular load is followed by `tl.trans` or another logical layout operation.
- A program owns one contiguous 2D output region but stores it through elementwise offsets.

### Profile

- Scalar or vector-side address, predicate, load, or store preparation is material relative to useful work.
- MTE pressure changes after an isolated pointer rewrite, suggesting that transfer shape or coordination changed.
- Treat ratios as routing evidence only; they do not prove that block-shaped DMA was generated.

### IR

Look for a mismatch between the logical tile and emitted memory operations:

- one rectangular source tile becomes many small loads or stores;
- address multiply/add, index casts, comparisons, or selects repeat per element or narrow vector;
- a contiguous output tile becomes multiple masked stores;
- a load is followed by a transpose or layout conversion that metadata might express;
- boundary predicates remain on an axis proven complete by dispatch;
- emitted transfer width is materially smaller than the contiguous logical region.

After rewriting, look for fewer or wider transfers, block-base plus block-advance addressing, removal of the targeted transpose/layout operation, fewer address/predicate operations, and boundary checks only on axes that can tail. IR operation names vary by stage, so compare structure rather than relying on one opcode string.

## Method

Confirm the fit first: the tile must be provably regular (logical axes,
physical strides, and tile ownership recorded; no address depends on runtime
data), and the parent lowering must actually show the degraded form —
fragmented, scalarized, or non-coalesced transfers — on a representative
case.

The optimization core is to rewrite one transfer at a time to
`tl.make_block_ptr`, keeping tile math, grid, precision, and all other
transfers fixed. Keep the rewrite only when the candidate IR changes that
specific form in the intended direction (fewer or wider transfers, block-base
plus block-advance addressing, the targeted transpose or layout operation
gone) and canonical latency improves; an unchanged IR or flat benchmark is a
useful negative result — pivot to the routed pattern instead of adding knobs.
Validate correctness on aligned and tail shapes, non-unit outer strides,
ragged boundaries, and the original padding semantics, and test ordinary
loading, transposed presentation, and output storage independently before
combining them.

### Candidate: Model a regular multidimensional tile

```diff
- rows = m0 + tl.arange(0, BLOCK_M)[:, None]
- cols = n0 + tl.arange(0, BLOCK_N)[None, :]
- tile = tl.load(x + rows * stride_m + cols * stride_n, mask=...)
+ ptr = tl.make_block_ptr(
+     base=x,
+     shape=(M, N),
+     strides=(stride_m, stride_n),
+     offsets=(m0, n0),
+     block_shape=(BLOCK_M, BLOCK_N),
+     order=(1, 0),
+ )
+ tile = tl.load(ptr, boundary_check=(0, 1), padding_option="zero")
```

### Candidate: Include a small inner dimension in the block

```diff
- for d in range(D):
-     vals = tl.load(x + pid * stride_pid + d * stride_d + tl.arange(0, BLOCK))
+ ptr = tl.make_block_ptr(
+     base=x, shape=(N, D), strides=(stride_n, stride_d),
+     offsets=(pid * BLOCK_N, 0), block_shape=(BLOCK_N, D), order=(1, 0),
+ )
+ vals = tl.load(ptr, boundary_check=(0, 1))
```

Update broadcasting and grid mapping together if the inner dimension was previously part of grid partitioning.

### Candidate: Present a transpose through metadata

When a dot consumer needs `K` presented as `(D, N)` while storage is packed as `(N, D)`, test whether metadata can express that presentation without a separate transpose:

```diff
- k = tl.load(k_ptrs, mask=k_mask, other=0.0)
- k_t = tl.trans(k)
+ k_ptr = tl.make_block_ptr(
+     base=k, shape=(D, N), strides=(stride_d, stride_n),
+     offsets=(0, n0), block_shape=(D, BLOCK_N), order=(0, 1),
+ )
+ k_t = tl.load(k_ptr, boundary_check=(1,), padding_option="zero")
```

This can help, remain flat, or regress depending on shape and existing lowering. The disappearance of `tl.trans` in source is not itself evidence of improvement.

### Candidate: Decompose a strided/subsampled axis by residue class

A strided traversal `x[:, r::stride]` does not present as a regular tile per program — it looks like a scattered-row gather, and the SIMT form may be slower than descriptor loads; compare the two forms on the target with equal work and shape. But each residue class `r` is itself a REGULAR affine array: rows `{r, r+stride, ...}` of a `[B, S, D]` buffer form a dense `[B, S_r, D]` view with row stride `stride * d_model`. Put the residue class in the grid and hand the descriptor the SCALED strides:

```diff
- # one program per (batch, head, m-tile), rows gathered individually
- rows = r + (m0 + tl.arange(0, BLOCK_M)) * stride
- tile = tl.load(x + b*s_b + rows[:, None]*s_s + cols[None,:], mask=...)
+ # grid gains a residue dimension: program = (batch, head, r, m-tile)
+ ptr = tl.make_block_ptr(
+     base=x + b * s_b + r * s_s,
+     shape=(S_r, D),                    # S_r = cdiv(S - r, stride)
+     strides=(stride * s_s, 1),         # scaled row stride
+     offsets=(m0, 0), block_shape=(BLOCK_M, D), order=(1, 0),
+ )
+ tile = tl.load(ptr, boundary_check=(0, 1), padding_option="zero")
```

`boundary_check` zero-fill then subsumes the per-class tail, the d masks, and any m-clamp/store-idempotence tricks the SIMT form needed (descriptor stores never write rows >= S_r). Structural masks (band/causal) re-express exactly in residue-local coordinates. The same applies to strided column slices of a packed projection buffer (see [`common-input-projection-packing`](common_input_projection_packing.md)): pass real strides, do not copy. Guard the shortest and the empty residue class (extent 0).

### Candidate: Use a contiguous 2D output store

If each program owns a contiguous `(BLOCK_M, D)` output tile, test a direct block-shaped store:

```diff
- tl.store(out + rows[:, None] * stride_m + cols[None, :] * stride_d,
-          acc, mask=out_mask)
+ out_ptr = tl.make_block_ptr(
+     base=out, shape=(M, D), strides=(stride_m, stride_d),
+     offsets=(m0, 0), block_shape=(BLOCK_M, D), order=(1, 0),
+ )
+ tl.store(out_ptr, acc, boundary_check=(0,))
```

## Related Patterns

- [`discrete-access-ub-staging`](discrete_access_ub_staging.md): use it for inherently data-dependent gather/scatter access rather than reinterpreting it as a dense tile.
- [`intermediate-layout-copy-deletion`](intermediate_layout_copy_deletion.md): use it when the main opportunity is removing a real layout materialization.
- [`implicit-transpose-elimination`](implicit_transpose_elimination.md): compare equivalent dot orientations when a
  regular block-pointer tile would otherwise own a costly logical transpose.
- [`program-multiple-rows`](program_multiple_rows.md): establish adjacent-row ownership when row-wise programs are too thin, then test a regular 2D transfer representation here. Grid ownership and transfer representation are separate decisions.
- [`software-pipeline`](software_pipeline.md): inspect compiler-generated buffering after regular block streaming is established.
- [`exact-tile-no-boundary-fast-path`](exact_tile_no_boundary_fast_path.md): remove boundary checks only after dispatch proves an axis complete.

## What To Verify After Applying

- The access is regular by semantics; no runtime-indexed gather or scatter was reinterpreted as a dense tile.
- Every `shape`, `strides`, `offsets`, `block_shape`, and `order` field matches the physical layout and consumer orientation.
- Parent and candidate preserve logical tile coverage, grid mapping, dtype, padding, and tail behavior.
- Parent evidence identifies the unexpected scalarized, fragmented, strided, or transpose-heavy form that motivated the experiment, or records lower confidence when IR is unavailable.
- Candidate IR changes that specific form in the intended direction; source simplification or the presence of a block pointer is not sufficient.
- Load, transposed presentation, and output store changes are benchmarked separately.
- Correctness and canonical latency improve or remain within the explicitly accepted tradeoff; profiler ratios alone are not treated as proof.
