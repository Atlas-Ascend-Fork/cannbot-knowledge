---
type: Optimization
title: Redundant-Loop Work Deletion
description: 用按证明有用范围限界的循环取代全范围 tile 循环加内部有用性守卫，删除剩余无用 tile 的工作。
tags: [task.optimization, topic.compute.reduction, topic.parallelism]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/redundant-loop-work-deletion.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Redundant-Loop Work Deletion

## Summary

Replace a full-range tiled loop plus an inner usefulness guard with a loop bounded by the proven useful extent. If the remaining useful tiles contain a fully valid region, a separate mask-free loop is a second, higher-risk candidate whose profitability depends on tile size, recurrence-body complexity, and Ascend lowering.

## Use When

A tiled loop iterates over a padded or maximum extent while the useful work
is shorter, so useless trailing iterations still pay loop control, loads,
recurrence, or pipeline work even though a guard suppresses their arithmetic:

```python
for tile_start in range(0, total_extent, BLOCK):  # full/padded range
    if tile_start < useful_extent:                # guard only skips the work
        ...  # loads, compute, recurrence updates
```

Runtime metadata or a loop-invariant predicate proves that the trailing tiles
are all inactive. A partially valid final tile can retain its exact boundary
predicate.

## Avoid When

- The useful frontier is an estimate rather than a proof.
- Skipped iterations have externally visible effects such as atomics, random-state updates, or synchronization state.
- Shortening the loop changes recurrence order or drops a partially valid tile.
- Empty, short, tail-heavy, or compiler-rejected shapes have no safe fallback.

## Signals

### Code

- A full-range loop contains `if tile_start < useful_extent` around most of its body.
- `useful_extent` is invariant during the loop and derivable from shape or runtime metadata.
- The body carries an accumulator, reduction, maximum, sum, counter, or buffer state across iterations.

### Profile

- Latency follows padded trip count rather than useful trip count.
- An inner guard suppresses arithmetic but does not remove the expected loop-time cost.
- Results vary strongly with tile size or with the complexity of the per-tile recurrence body.

## Start With the Basic Transformation

### Replace a Guard with a Bound

The common parent iterates over the full physical or padded extent and guards the useful body:

```python
acc = initial_accumulator()

for tile_start in range(0, total_extent, BLOCK):
    if tile_start < useful_extent:
        offsets = tile_start + tl.arange(0, BLOCK)
        boundary = offsets < useful_extent
        values = tl.load(input_ptr + offsets, mask=boundary, other=0.0)
        acc = update(acc, values)
```

Move the proven frontier into the range:

```python
acc = initial_accumulator()

for tile_start in range(0, useful_extent, BLOCK):
    offsets = tile_start + tl.arange(0, BLOCK)
    boundary = offsets < useful_extent
    values = tl.load(input_ptr + offsets, mask=boundary, other=0.0)
    acc = update(acc, values)
```

The boundary predicate remains necessary for the final partial tile. The optimization changes the number of recurrence trips; it does not make the final tile fully valid.

### Concrete trip-count example

Suppose:

```text
total_extent  = 4096
useful_extent = 1025
BLOCK         = 128
```

The guarded full loop takes:

```text
ceil(4096 / 128) = 32 trips
```

The bounded loop takes:

```text
ceil(1025 / 128) = 9 trips
```

Trips 0 through 7 are complete. Trip 8 begins at 1024 and keeps a lane predicate for the one useful element. Trips 9 through 31 disappear entirely, including their loop control and any recurrence or pipeline work that an inner guard failed to remove.

### Proof obligation

For a tile beginning at `tile_start`, suffix deletion requires:

```text
tile_start >= useful_extent
=> every lane in this and all later tiles is inactive
=> loads, compute, and recurrence updates have no semantic effect
```

Clamp `useful_extent` to the physical extent. Do not round it down unless the omitted partial tile is processed separately.

## Dynamic Zero-Trip Loops and First-Tile Peeling

A runtime bound may be zero. A loop-carried accumulator must then have a valid value without executing the body. Ascend lowering can introduce conditional initialization or extra state to support that possibility.

First verify whether zero useful tiles are valid inputs. If zero trips are impossible by contract, express or specialize that fact instead of adding a fallback. If zero trips are valid and the common case has at least one tile, first-tile peeling is a measured alternative:

```python
has_tile = useful_extent > 0
first_offsets = tl.arange(0, BLOCK)
first_boundary = first_offsets < useful_extent
first_values = tl.load(
    input_ptr + first_offsets,
    mask=has_tile & first_boundary,
    other=0.0,
)
first_acc = update(initial_accumulator(), first_values)
acc = tl.where(has_tile, first_acc, empty_result())

for tile_start in range(BLOCK, useful_extent, BLOCK):
    offsets = tile_start + tl.arange(0, BLOCK)
    boundary = offsets < useful_extent
    values = tl.load(input_ptr + offsets, mask=boundary, other=0.0)
    acc = update(acc, values)
```

Peeling is not automatically faster. It may replace dynamic loop initialization with a predicated first body, but can add duplicated code, a branch/select, and a special empty-result path. Compare peeled and unpeeled bounded versions under the same tile and body, and inspect whether later IR actually becomes simpler.

## Region Splitting: A Separate, Riskier Candidate

After suffix deletion, some executed tiles may need no semantic predicate while a final region remains partial. The one-loop bounded version is:

```python
acc = initial_accumulator()

for tile_start in range(0, useful_extent, BLOCK):
    offsets = tile_start + tl.arange(0, BLOCK)
    valid = semantic_predicate(offsets, metadata)
    values = tl.load(input_ptr + offsets, mask=physical_mask(offsets), other=0.0)
    acc = update(acc, tl.where(valid, values, neutral_value()))
```

A region-split candidate is:

```python
acc = initial_accumulator()

for tile_start in range(0, fully_valid_end, BLOCK):
    offsets = tile_start + tl.arange(0, BLOCK)
    values = tl.load(input_ptr + offsets, mask=physical_mask(offsets), other=0.0)
    acc = update(acc, values)

for tile_start in range(fully_valid_end, useful_extent, BLOCK):
    offsets = tile_start + tl.arange(0, BLOCK)
    valid = semantic_predicate(offsets, metadata)
    values = tl.load(input_ptr + offsets, mask=physical_mask(offsets), other=0.0)
    acc = update(acc, tl.where(valid, values, neutral_value()))
```

`fully_valid_end` must be the largest tile boundary for which every element processed by the first body is semantically valid. Physical load/store masks may still be needed even when the semantic predicate is unnecessary.

This split does **not** delete more useful recurrence trips. It trades mask/control work in the fully valid region for an additional recurrence loop and state transfer between loops. Test it only after the basic guard-to-bound rewrite is correct and measured.

A recurrence loop carries values such as accumulators, maxima, sums, counters, or buffer state. Splitting one loop into two can require separate lowering structures and explicit connection of their live state.

Possible costs include:

- conditional initialization when either region may execute zero times;
- more loop-carried values and induction state;
- duplicated Cube/Vector operation regions or pipelines;
- longer local-buffer lifetimes or extra buffer selection;
- additional waits, barriers, or multi-buffer management;
- changed layout, fixpipe path, or resource legality.

The removed predicate may be cheaper than these costs. The same split can therefore regress with a heavy recurrence body and win with a simpler body.

Describe body complexity structurally: count dots, reductions, conversions, loop-carried dependencies, live tensors, and synchronization points. Do not encode one operator or one winning implementation as a universal enabling condition.

## Tile-Coupled Selection

For each tile candidate, estimate:

```text
full_trips       = ceil(total_extent / BLOCK)
useful_trips     = ceil(useful_extent / BLOCK)
deleted_trips    = full_trips - useful_trips
trip_reduction   = deleted_trips / full_trips
```

Compute counts per program and across the representative workload.

- A larger tile makes each deleted trip more valuable but increases live shapes, tail waste, and local-memory pressure.
- A smaller tile may compile more easily but makes each deleted trip cheaper and repeats control and recurrence work more often.
- Changing an ownership-axis tile can also change program count, data reuse, and program batching.

## Cost Model

For guard-to-bound deletion:

```text
parent cost ≈ full trips   × parent per-trip cost + parent fixed cost
child cost  ≈ useful trips × child per-trip cost  + child fixed cost
```

For region splitting:

```text
split cost ≈ useful tile work
           - removed predicate/control work
           + additional loop/pipeline/state-management cost
```

A shorter loop or mask-free region proves that source work changed. It does not prove lower runtime.

## Attribution Experiments

Loop structure, recurrence body, and tile size each change the outcome.
Change one factor per comparison and keep tile, grid, pointer
representation, semantic predicates, warps, stages, compiler options,
inputs, and the timing contract fixed otherwise.

### Body × loop structure

| Variant | Body | Loops | Compare against | Question answered |
|---------|------|-------|-----------------|-------------------|
| control | current | one loop | — | — |
| split-only | current | split loops | control | Does splitting pay with the current body? |
| body-only | proposed | one loop | control | Is the body rewrite independently useful? |
| both | proposed | split loops | body-only | Does splitting pay with the proposed body? |

If split-only regresses but the combined variant beats body-only, do not
record "loop splitting wins"; record that region splitting is enabled by the
tested body class and describe what became structurally simpler. The proposed
body must independently satisfy correctness and numerical contracts — lower
precision is not acceptable merely because it enables a faster split.

### Tile × loop bound

For a small and a large legal tile, compare the guarded full loop with the
bounded loop at the same tile (parent-small, child-small, parent-large,
child-large) and interpret each tile separately: comparing only the two
bounded candidates confounds tile selection with loop deletion. For region
splitting, first use the best-understood legal tile and expand the tile
search only after identifying which body/loop combination is profitable.

## IR Verification

Compare each parent/child pair under the same target and configuration.

### Guard-to-bound

The intended TTIR change is:

```diff
- scf.for %tile = 0 to %total_extent step %BLOCK {
-   scf.if %tile_lt_useful { ... recurrence ... }
+ scf.for %tile = 0 to %useful_extent step %BLOCK {
+   ... recurrence ...
```

Verify in later IR that:

- the algorithmic recurrence still has the shorter logical bound;
- no full-range helper recurrence recreates deleted work;
- conditional initialization, buffers, waits, or barriers added for the dynamic bound are explained;
- per-tile Cube/Vector paths and local-memory requirements remain legal;
- static operation counts are reconciled with runtime trip counts.

### Region splitting

Verify that:

- the fully valid loop has no semantic predicate or compensating `where`;
- the boundary loop retains the original predicate;
- both loops carry recurrence state in the correct order;
- added loops, conditionals, transfers, waits, barriers, or duplicated Cube/Vector regions — the costs listed under Region Splitting — are explained;
- static duplication of a body is distinguished from its runtime trip count.

IR is diagnostic evidence. Do not request compiler attributes mechanically from Triton source.

## Decision Procedure

1. Prove the useful frontier and partial-boundary semantics (see Proof obligation).
2. Replace the guard with a bounded loop, keeping body, tile, and boundary predicate fixed.
3. Validate empty, one-tile, aligned, unaligned, and representative long extents.
4. Compare guarded and bounded loops per legal tile with repeated paired measurements (see Attribution Experiments).
5. If zero-trip initialization looks costly, test first-tile peeling against the unpeeled bounded loop.
6. Keep suffix deletion only for tile/shape regimes that improve the target metric.
7. If fully valid tiles still execute material predicate work, evaluate region splitting through the attribution experiments — including all four body×loop variants when the body also changes.
8. Capture TTIR and later IR for each relevant pair and explain added loop, pipeline, state, and resource costs.
9. Preserve guarded or one-loop fallbacks for neutral, slower, or compiler-illegal regimes.

## Interpreting Results

- Correctness failure means the frontier, boundary, recurrence order, peeling, or proposed body is invalid.
- Correctness passes but TTIR retains the full bound: guard-to-bound deletion was not expressed or preserved.
- TTIR shortens but later IR becomes more expensive: dynamic-bound lowering defeats that tile/body candidate.
- First-tile peeling loses: keep the simpler bounded loop; zero-trip support was not the dominant cost.
- For body×split outcomes, read the attribution table: a split that wins only with the proposed body stays tied to that body class.
- IR is comparable but latency is unchanged: too little work was removed or the effect is below measurement sensitivity.

A negative result rejects the tested source form, tile, body, shape regime, compiler configuration, and metric. Retry only after naming which causal condition changed.

## Related Patterns

- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): derive attention-specific visibility frontiers and tile classes.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): isolate tile, precision, and live-shape conditions that affect resource legality.
- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): separate algorithmic-loop changes from launch and physical-core work distribution.
- [ragged-tile-early-return](./ragged_tile_early_return.md): delete a whole program body whose tile lies outside a segment-local extent, rather than deleting invalid iterations inside one live program.

## What To Verify After Applying

- Every deleted tile is inactive, and every partial boundary keeps the exact semantic predicate.
- Parent and child use the same benchmark contract and controlled configuration.
- The bounded child has fewer algorithmic recurrence trips in TTIR and no compensating full-range recurrence later.
- Peeling is compared directly with the unpeeled bounded loop when used.
- Multi-loop candidates retain the explicit current-body/proposed-body comparisons.
- Proposed body correctness is validated independently from loop-structure correctness.
- Per-tile lowering and resource legality remain acceptable.
- Results are reported by tile, body, shape regime, kernel latency, and total-operation latency.
- Compiler revision, target, flags, trip counts, and repeated paired measurements are recorded.
