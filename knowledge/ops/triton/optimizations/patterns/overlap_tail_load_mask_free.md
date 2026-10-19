---
type: Optimization
title: Overlap Tail Load for Idempotent Reductions
description: 行/段幂等归约在 BLOCK < length ≤ 2·BLOCK 且不对齐时，重叠加载尾块并免 mask 合并计算。
tags: [task.optimization, topic.compute.reduction, topic.implementation.masking]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/overlap-tail-load-mask-free.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Overlap Tail Load for Idempotent Reductions

## Summary

When a **row- or segment-wise idempotent reduction** (max, min, argmax, argmin, any, all) has `BLOCK < length <= 2 * BLOCK` with `length % BLOCK != 0`, cover it with two **unmasked** loads — a main tile `[0, BLOCK)` and an overlapping tail tile `[length-BLOCK, length)` — instead of one masked tail tile. For longer rows, keep the full middle tiles and overlap only the final partial tile. Overlapped elements participate twice, which is harmless because idempotent reductions tolerate duplicates and position-aware tie-breaking (`smaller pos wins`) preserves the true first occurrence. This removes the masked-load lowering (conditional whole-tile fill plus copy on Ascend) from the hot path.

## Use When

A row- or segment-wise idempotent reduction (max, min, argmax, argmin, any,
all) runs on rows whose length is not a multiple of `BLOCK`, so the final
tile is masked. A typical example:

```python
cols = tl.arange(0, BLOCK)
vals = tl.load(row_ptr + cols, mask=cols < n, other=float("-inf"))  # final tile
row_max = tl.max(vals, axis=0)
```

IR shows the masked tail load lowered to a conditional whole-tile fill plus
copy on the hot path. For argmax/argmin, ties are already resolved by
position (the smaller position wins), so visiting an element twice cannot
change the result.

The rewrite covers the tail with two overlapping unmasked tiles —
`[0, BLOCK)` and `[length-BLOCK, length)` — so the masked load disappears
from the hot path.

## Avoid When

- **Sum, mean, norm, count, or any non-idempotent reduction**: overlapped elements would be double-counted. Do not apply to softmax's exp-sum pass, rms/layer-norm sums, histograms, or counting.
- `length <= BLOCK` — nothing to overlap; use a single masked or padded-layout tile instead.
- Copy, stencil, or data-movement kernels — duplicated elements corrupt output.
- The masked path is cold (only boundary programs execute it); overlap then just adds a redundant load.

## Signals

### Code

- `tl.load(..., mask=cols < n, other=...)` on a single tile or last tile inside a max/argmax row kernel whose length is a runtime shape like 1023/2049/4001.

### IR

- `scf.if` + `linalg.fill` before `memref.copy` in the load lowering of the hot loop or single-tile kernel.

## Method

Confirm the fit first: IR must show the masked tail load lowered to conditional fill plus copy on the hot path, and the reduction must be idempotent with position-aware tie-breaking.

The optimization core is to cover the row with two unmasked overlapping tiles instead of one masked tail tile, so the mask disappears from the hot path. Compare the overlap form against the masked form on the target harness before keeping it.

### Rule: Cover the tail with two overlapping unmasked loads

For `BLOCK < length <= 2 * BLOCK`, load tile A at `[0, BLOCK)` and tile B at `[length-BLOCK, length)`, both unmasked. For longer rows, retain the full middle tiles and apply this overlap only to the final partial tile.

```python
a = tl.load(row_ptr + cols)                 # [0, BLOCK)
b = tl.load(row_ptr + (n - BLOCK) + cols)   # [n-BLOCK, n)
```

### Rule: Combine tiles with position-aware tie-breaking

Reduce each tile independently to (value, first-pos) candidates, then combine with `take = mvB > mvA` so equal values keep the earlier true position.

### Rule: Keep a masked branch for partial programs

Programs that are only partially in range (incomplete rows/blocks) keep a divergent masked branch:

```python
if (pid + 1) * BLOCK_M <= n_rows:
    # unmasked two-tile path
else:
    # masked path covering BOTH segments: [0, BLOCK) and [BLOCK, n)
```

The masked branch must cover both segments. Covering only `[0, BLOCK)` silently drops `[BLOCK, length)` — benches that only time will pass while correctness fails.

### Rule: Do not replace masks with clamped indices

Data-dependent clamped addresses degrade the load into a gather on Ascend, so clamping is not a substitute for the overlap form.

## What To Verify After Applying

- Rows/blocks handled by the **last** (partial) program, with extrema located in the middle gap, the overlap, and the tail; a branch that masks only the first segment can silently miss valid indices.
- The reduction is genuinely idempotent for the emitted outputs (index ties resolved by position, not visit order).
- Length edges: `length == BLOCK`, `length == BLOCK + 1`, `length == 2 * BLOCK`.

## Related Patterns

- [mask-only-affine-addressing](./mask_only_affine_addressing.md) — the correct repair when a clamp is already present; it keeps the mask and deletes only the clamp, which is bit-exact and works for non-idempotent reductions too.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md) — divisibility-based mask elimination; overlap-load is the non-divisible-length counterpart for idempotent reductions.
- [live-length-tiling](./live_length_tiling.md) — exact (possibly non-pow2) tile lengths when one tile suffices instead of two overlapping tiles.
- [packed-key-argmax-single-reduction](./packed_key_argmax_single_reduction.md) — the position-aware tie-breaking that makes overlap duplicates harmless.
