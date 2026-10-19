---
type: Optimization
title: Ragged Tile Early Return
description: 当权威段元数据证明整个 program tile 落在有效矩形之外时，在 tile 内工作前提前返回。
tags: [task.optimization, topic.tiling, topic.implementation.masking]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/ragged-tile-early-return.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Ragged Tile Early Return

## Summary

Return before tile-local work when authoritative segment metadata proves that
an entire program tile lies outside the segment's valid rectangle. Keep the
ordinary masked body for partial edge tiles. Treat entry elision and compact
live-task submission as separate experiments.

## Use When

The kernel processes ragged data: a batch of variable-length segments, such
as the sequences in a varlen LLM batch. It launches a padded rectangular
grid sized to the longest segment, so each segment spans multiple program
tiles while its true length is smaller and known only at runtime. Tiles that
fall completely outside their segment's valid rectangle still execute the
tile body before a final all-false mask discards every lane:

```python
offs = row_begin + tl.arange(0, BLOCK_ROWS)
mask = offs < local_rows              # per-lane mask only, no whole-tile guard
x = tl.load(ptr + offs, mask=mask)    # runs even when row_begin >= local_rows
```

The per-segment lengths (metadata such as `cu_seqlens`) are available before
tile data is accessed, so they can prove a whole tile invalid. Profiling
shows kernel time tracking the padded grid area rather than the sum of live
per-segment tiles.

## Avoid When

- The proposed guard can prove only that some lanes are invalid; partial edge
  tiles still require the original per-lane masks.
- Programs must participate in atomics, synchronization, random-state
  advancement, counters, or another observable action before the return.
- Segment bounds are estimates, captured examples, or stale host constants
  rather than authoritative metadata for the current invocation.
- The apparent waste is only inactive lanes inside otherwise useful programs;
  use `live-length-tiling` or another boundary refinement instead.
- The expensive body is already control-dependent on a whole-tile predicate,
  or the launch already submits only live segment-local tiles.
- Removing or compacting programs would eliminate independent work needed to
  hide a long reduction or recurrence. Measure occupancy before replacing the
  rectangular launch.

## Signals

### Code

- The grid uses global tile counts and decodes a segment before loading its
  local row or column length.
- Lane masks are constructed from local lengths, but there is no scalar guard
  on the tile origin before vector ranges and predicate work are created.
- A tile interval has no intersection with the segment's useful rectangle, but
  the implementation still constructs vector ranges, packed indices, or block
  pointers before rejecting it.

### Profile

- A large submitted-program population performs little or no useful output
  work while vector activity remains material and transfer activity is low.
- Across shapes, elapsed time tracks the share of wholly invalid programs more
  closely than partial-tail padding alone predicts.

### IR

- Whole-invalid programs can still reach vector compares, broadcasts, selects,
  packing, arithmetic, or transfer preparation after local bounds are known.
- In the candidate, the expensive region is control-dependent on a cheap
  scalar whole-tile guard.
- Address lowering is already affine or regular, ruling out true gather or
  scatter as the primary explanation for the Vector work.
- The guard has no cross-program dependency, barrier, or required reduction
  participation that would prevent an early return from compiling.

## Problem

A false store mask guarantees memory safety and output semantics, but it does
not guarantee that the compiler removes the computations that produced the
stored value or mask. In a maximum-sized ragged grid, programs outside one
segment's live rectangle can therefore execute nearly the complete tile body
and discard every lane only at the end.

This is different from an ordinary partial tail. A partial edge tile contains
useful lanes and must keep exact row and column masks. Only a tile whose
origin is beyond at least one authoritative local length is eligible for
whole-program elision.

## Method

Confirm the fit first: derive launched tile counts from the actual grid and
classify programs as fully useful, partially useful, or wholly invalid from
exact runtime segment metadata, not from Block Dim or aggregate engine
ratios. Profile and IR evidence must connect the wasted work to the padded
rectangular launch rather than only to partial boundary tiles.

The optimization core is a cheap scalar guard that returns before any
tile-local work when the tile origin lies outside the segment's valid
rectangle. Build the guard from the rules below; keep the original masked
body unchanged for every intersecting tile.

### Rule: Prove whole-tile invalidity from authoritative runtime metadata

Derive local lengths from the same runtime segment metadata that defines
pointer bases and semantic boundary masks. Do not replace them with captured
length tables or a benchmark-specific layout switch. If a host specialization
is added later, it must validate every runtime property behind the proof and
keep a generic fallback.

### Rule: Return before any tile-local vector work

Compute only the scalar tile origins needed for the proof, then return before
constructing vector ranges, IDs, predicates, temporaries, or transfers. A
guard placed after `tl.arange` or tile loads keeps most of the wasted work.
Axis names and metadata sources follow the operator's actual segmentation
contract:

```diff
 row_begin = tile_row * BLOCK_ROWS
 col_begin = tile_col * BLOCK_COLS
+if row_begin >= local_rows or col_begin >= local_cols:
+    return
+# Existing partial-tile masks and tile body remain below.
 offs = row_begin + tl.arange(0, BLOCK_ROWS)
```

### Rule: Keep the original masked path for every intersecting tile

A tile is elidable only when its origin is beyond at least one authoritative
local length. First and last partial tiles must keep their causal, window,
ID, padding, and other semantic masks exactly; treating a partially valid
tile as empty silently drops outputs.

### Rule: Measure entry elision separately from compact live-task submission

The guard removes tile-body cost but not launch and scalar-entry cost. Measure
the low-risk body elision first, on the same tile and grid, so the result is
attributable. Only if residual program submission or program-batch imbalance remains
material, evaluate compact live-task mapping through
`engine-aware-grid-scheduling` as a separate change.

## Cost Model

For each segment, compare launched rectangular work with tiles that intersect
the live rectangle:

```text
launched = ceil(global_rows / block_rows) * ceil(global_cols / block_cols)
live     = ceil(local_rows / block_rows) * ceil(local_cols / block_cols)
```

The guard removes the body cost of `launched - live` programs, but it does not
remove their launch and scalar-entry cost. First measure this low-risk body
elision. If residual program submission or program-batch imbalance remains material,
then evaluate compact live-task mapping through
`engine-aware-grid-scheduling` as a separate change.

## Failure Modes

- Moving the return after `tl.arange`, predicate construction, or tile loads
  preserves most of the wasted work.
- Treating a partially valid tile as empty silently drops outputs.
- Hard-coded segment fingerprints can pass captured cases while skipping valid
  work for a new length distribution.

## Related Patterns

- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): remove whole-invalid programs from the
  submitted domain after entry elision establishes the opportunity.
- [live-length-tiling](./live_length_tiling.md): reduce padded lanes inside tiles that still
  intersect the live length.
- [redundant-loop-work-deletion](./redundant_loop_work_deletion.md): delete invalid loop iterations inside
  one live program rather than deleting a whole program body.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): derive semantic visibility for attention tiles;
  this card applies to segment-local geometric emptiness in any ragged grid.
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md): retain the padded fallback when the
  guard or compact mapping is profitable only in a causal shape regime.
- [mask-only-affine-addressing](./mask_only_affine_addressing.md): apply only when IR proves regular addressing
  was lowered to indirect access; regular affine IR is a non-match.

## What To Verify After Applying

- Empty, one-tile, exact-multiple, partial-edge, multi-segment, and highly
  uneven inputs preserve complete output coverage with no duplicate or skipped
  live tile. Include different segment distributions with the same global
  maxima.
- Metadata loads used by the guard are valid before any early return and match
  the public segmentation contract for the current invocation.
- Source and generated IR place vector and transfer work after the whole-tile
  guard; partial tiles still execute the complete semantic mask.
- Measure launched, fully useful, partially useful, and wholly invalid program
  counts by shape without turning observed values into dispatch constants.
- Compare the same tile and grid before and after entry elision, then measure
  the complete public operation under the canonical metric, including every
  producer and consumer launch when a split writes an intermediate to memory.
- For a compact-grid follow-up, verify task decoding, output ownership, grid
  size, program-batch occupancy, and both short- and long-reduction regimes separately.
