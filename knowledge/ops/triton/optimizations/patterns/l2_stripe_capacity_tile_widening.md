---
type: Optimization
title: L2 Stripe-Capacity Tile Widening
description: 当 GEMM 类 kernel 每 program batch 的长轴操作数切片超出 L2 容量导致吞吐坍塌时，加宽 tile 降低重读次数。
tags: [task.optimization, topic.memory, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/l2-stripe-capacity-tile-widening.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# L2 Stripe-Capacity Tile Widening

## Summary

When a GEMM-like kernel's per-program-batch slice of a long-axis operand exceeds L2 capacity, throughput collapses over a cliff; widening the tile along the other dimension divides that operand's HBM re-read count and restores cube-bound throughput.

## Use When

A tiled `tl.dot` GEMM or batched matmul reaches near-peak throughput on
moderate sizes but collapses sharply once one operand's long axis (say N)
grows past a
threshold — a large-factor cliff, not a gradual slope. The tiling code is a
standard 2-D GEMM grid whose `BLOCK_M` and `BLOCK_N` were tuned on small
shapes and never revisited for the large-size regime:

```python
# tuned on small shapes; N now huge
grid = (triton.cdiv(M, BLOCK_M) * triton.cdiv(N, BLOCK_N) * BATCH,)
```

The re-read accounting explains the cliff: each M-side panel is re-read
`N / BLOCK_N` times and each N-side panel `M / BLOCK_M` times, so the slice
of the N-side operand that one program batch touches per pass grows with N
until it is comparable to or larger than L2.

## Avoid When

- UB planning rejects the widened tile — the lever trades UB for L2 reuse; if the wider tile does not fit, apply `large-tile-fit-enabling` or change program order (`diagonal-block-traversal`, `engine-aware-grid-scheduling`) instead.
- Widening shrinks the grid below the physical core count (small M): the kernel becomes latency-bound and loses more from idle cores than it gains from L2 reuse.

## Signals

### Profile

- A throughput-vs-size curve with a sharp cliff at an L2-plausible stripe footprint rather than a smooth decline.
- HBM read bytes per output element growing linearly past the cliff while cube utilization collapses.

## Method

Confirm the fit first: measure achieved TF (or effective HBM bytes per output
element) across the long-axis length (say N) at a fixed tile. A sharp knee
near an L2-plausible stripe footprint distinguishes L2 collapse from a smooth
latency slope — do not retile on a smooth curve.

The optimization core is the re-read accounting: with `(BLOCK_M, BLOCK_N)`
tiles, each M-side panel is re-read `N / BLOCK_N` times and each N-side
panel `M / BLOCK_M` times, so the lever for the N side is the *other* tile
length. Widen the tile along the M dimension (typically `BLOCK_M` when N is
the huge axis) until the per-batch slice fits L2
or UB planning rejects the wider tile.

### Rule: Widen the tile along the reused dimension by regime dispatch

Keep the small-shape tile for small sizes and select the widened tile only
past the measured knee:

```python
# host-side regime dispatch; keep the small-shape tile for small N
BLOCK_M = 256 if N >= L2_CLIFF_N else 128   # knee measured per target
grid = (triton.cdiv(M, BLOCK_M) * triton.cdiv(N, BLOCK_N) * BATCH,)
```

Recovery is largest just past the cliff; shapes far beyond it remain
bandwidth-bound and gain less.

### Rule: Check the hard constraints after each widening step

Two constraints bound the lever: UB planning must still succeed for the wider
tile (if not, see `large-tile-fit-enabling`), and the grid must stay at or
above the physical core count at the smallest benchmark shape — otherwise
idle cores cost more than L2 reuse gains.

### Rule: Change only the tile on the first comparison

Keep the kernel body, traversal order, and `BLOCK_K` byte-identical so the
first comparison isolates the tile effect; compose with
`diagonal-block-traversal` or grouped order only afterwards. The rewrite
changes only which output elements a program computes, so results are
bit-exact for a fixed `BLOCK_K`; a numerical diff after this change means
something else moved.

This card is the tile-shape half of the L2 problem; `diagonal-block-traversal`
is the program-order half. The two compose: tile aspect ratio bounds the
total re-read count, traversal order bounds the per-batch footprint. If even
the widened tile cannot close the gap to a tuned reference implementation on
the same shapes, the residual gap is the decision input for offloading the
stage (`kernel-fusion-and-value-placement`), not a reason to keep tuning.

## Related Patterns

- [diagonal-block-traversal](../techniques/core_mapping.md): program-order remap for L2 locality and bank conflicts — the orthogonal half.
- `tiling` and [large-tile-fit-enabling](./large_tile_fit_enabling.md): UB-side capacity and whether the widened tile fits.
- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): per-batch mapping; keep tile math fixed there, change it here.
- [现有知识：Bank Conflict 消除](../techniques/bank_conflict.md)
- [现有知识：Core 映射策略](../techniques/core_mapping.md)

## What To Verify After Applying

- Correctness on masked tails introduced by the new tile shape.
- Throughput on the previously collapsing shapes, plus a regression check on the moderate shapes the old tile was tuned for.
- Grid size still >= physical core count at the smallest benchmark shape.
