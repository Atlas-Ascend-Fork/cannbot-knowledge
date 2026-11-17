---
type: Optimization
title: 独立 Load 位置消融
description: 在真实数据依赖允许时移动独立 load，以等量工作的对照实验验证流水改善。
tags:
- task.optimization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/independent-load-placement.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Independent Load Placement Experiment

## Summary

Test alternative source placements for independent loads as compiler scheduling hypotheses. Emitted transfer order and coordination, together with measured latency, decide whether a candidate helps.

## Use When

Your hot kernel issues several loads that do not depend on each other, and
their source order could change without changing any address, mask, or value.
The typical shape is a dominant tile load sitting next to small scale, weight,
bias, or metadata loads:

```python
x = tl.load(x_ptr + x_offsets)          # dominant tile load
scale = tl.load(scale_ptr + s_offsets)  # small parameter loads
weight = tl.load(weight_ptr + w_offsets)
```

The profile shows memory latency, transfer coordination, or on-chip buffer
pressure contributing materially to kernel latency. You can inspect the
generated IR or device code and benchmark each placement candidate.

## Avoid When

- A moved load has a true address, data, control, alias, or required side-effect dependency on an operation it would cross.
- Correctness depends on ordering with an overlapping store or atomic operation.
- Tile shape, traversal, math, fusion boundaries, or stores cannot be held fixed for the comparison.
- Benchmark noise is too large to distinguish the candidates.

## Signals

### Code

- Independent dense and indexed loads appear in the same hot region.
- A dominant tile load and several small parameter loads can be placed in either order without changing results.
- Source placement changes are small enough to test as one-variable ablations.

### Profile

- Transfer waits, memory stalls, or low overlap contribute materially to latency.
- UB or register pressure may limit how early a loaded value should become live.
- Performance changes by shape, especially when the dominant transfer grows.

### IR

- Emitted load order or set/wait coordination differs between candidates.
- Fusion changes or a value is written to memory after a load moves.
- Live ranges, spills, or UB allocation differ even when transfer order does not.

## Method

Confirm the fit first: trace each candidate load's pointer operands, mask,
control predicates, and every memory effect it would cross, and prove the
ranges cannot alias or that their ordering is irrelevant. A real address
dependency cannot be reordered: `idx = tl.load(index_ptr)` must precede
`tl.load(table_ptr + idx)`, because the indexed load depends on the value of
`idx`. Preserve atomics and required store-to-load ordering. Record tile
shape, traversal, math, masks, and store placement as the fixed control
baseline.

The optimization core is to move exactly one independent load relative to the
surrounding operations, then benchmark that single change. Neither placement
is universally better: an earlier load may let lowering schedule its transfer
sooner or overlap it with other work, or it may lengthen a live range,
increase UB pressure, alter fusion, or produce no lowering change at all.
Keep a candidate only when the emitted loads, fusion, set/wait coordination,
or live ranges changed as hypothesized and repeated end-to-end timing improves.

### Candidate: Dense load around an indexed chain

An independent dense tile load may be placed before, between, or after the
operations of an indexed-address chain when its address and memory range are
independent and alias-safe:

```diff
-idx = tl.load(index_ptr)
-indexed = tl.load(table_ptr + idx)
-dense = tl.load(dense_ptr + dense_offsets)
+dense = tl.load(dense_ptr + dense_offsets)
+idx = tl.load(index_ptr)
+indexed = tl.load(table_ptr + idx)
```

The same test applies inside a loop:

```diff
 for i in range(HEAD_NUM):
+    b_A = tl.load(p_A)   # A assumed not to alias B
     idx_B = tl.load(B_index_ptr + i)
     b_B = tl.load(B_ptr + idx_B + offsets)
-    b_A = tl.load(p_A)
```

`idx_B` does not depend on the prior-iteration B store. A loop-carried
dependency exists only between iteration `i - 1`'s store to
`B_ptr + idx_B_prev + offsets` and iteration `i`'s load from
`B_ptr + idx_B + offsets`, and only when those ranges overlap. Because A does
not alias B, moving its load earlier is a compiler scheduling candidate, not a
promise of earlier issue, overlap, fewer cycles, or speedup. If consecutive B
ranges never overlap, the loop-carried dependency does not apply and ordinary
independent-load placement can still be tested.

### Candidate: Dominant tile versus small parameters

Hold tile shape and traversal fixed while comparing dominant-tile-first
against small-parameters-first:

```diff
-x = tl.load(x_ptr + x_offsets)
-scale = tl.load(scale_ptr + scale_offsets)
-weight = tl.load(weight_ptr + weight_offsets)
-bias = tl.load(bias_ptr + bias_offsets)
+scale = tl.load(scale_ptr + scale_offsets)
+weight = tl.load(weight_ptr + weight_offsets)
+bias = tl.load(bias_ptr + bias_offsets)
+x = tl.load(x_ptr + x_offsets)
```

Transfer engines, fusion, set/wait placement, cache behavior, and live ranges
can favor either candidate for a particular kernel and shape. Do not infer a
largest-first rule from transfer size alone.

### Candidate: Traversal direction

Traversal direction is a separate variable, not load order. When testing
direction, hold intra-iteration load placement fixed; when testing load
placement, hold traversal direction fixed.

```diff
-for tile in range(0, n_tiles):
+for rev in range(0, n_tiles):
+    tile = n_tiles - 1 - rev
     x = tl.load(x_ptr + tile * TILE + offsets)
     # unchanged intra-iteration loads and math
```

Forward and reverse traversal may expose different prefetch, cache, or
coordination behavior, but direction must be benchmarked as its own ablation.

### Discipline

Do not promote a universal load order from one workload. Move one load at a
time while holding tile shape, traversal, math, masks, and stores fixed; run
correctness checks and benchmark representative shapes with repeated
measurements. Retain no source-order story unsupported by emitted code and
measurements.

## Related Patterns

- [Software Pipeline](software_pipeline.md) for explicit overlap across loop iterations.
- [Intermediate Layout Copy Deletion](intermediate_layout_copy_deletion.md) when placement changes expose conversion or intermediate-copy costs.
- [Engine-Aware Grid Scheduling](engine_aware_grid_scheduling.md) when grid-level transfer pressure dominates local placement.

## What To Verify After Applying

- The moved load is independent and alias-safe across every crossed operation.
- Indexed address chains, atomics, and required memory ordering remain intact.
- Emitted transfer order, fusion, set/wait coordination, or live ranges changed as hypothesized.
- Correctness holds for boundary, masked, aliased-risk, and representative production shapes.
- Latency improves consistently; retain no source-order story unsupported by emitted code and measurements.
