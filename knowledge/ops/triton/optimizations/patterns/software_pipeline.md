---
type: Optimization
title: Compiler-Aware Software Pipelining
description: 检查编译器生成的缓冲与搬运-计算协同，把手动 carry 或文本 prefetch 当作调度消融，仅在证据支持时保留。
tags: [task.optimization, topic.implementation.pipeline, topic.data_movement.memory_access]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/software-pipeline.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Compiler-Aware Software Pipelining

## Summary

Inspect compiler-generated buffering and transfer-compute coordination in regular tiled loops. Treat manual carry or textual prefetch as a scheduling ablation, and retain it only when generated scheduling evidence and benchmarks attribute a real improvement.

## Use When

A hot regular tiled loop loads independent tiles and computes on them in
load-then-compute order:

```python
for _ in range(num_k_tiles):
    a = tl.load(a_ptr)
    acc = tl.dot(a, b, acc)
    a_ptr = tl.advance(a_ptr, (0, BLOCK_K))
```

Profiling shows engine idle time or Task Wait around the loop, or generated
IR lacks clear transfer-compute coordination. Each iteration has enough work
that overlapping the next tile's transfer with current-tile compute could
pay off. Compiler-reported usable UB leaves room for the extra buffers and
live values an overlapped schedule needs.

Pipelining the loop — prefetching the next tile while computing the current
one — hides the transfer latency behind compute.

## Avoid When

- A recurrence or data dependency prevents loading the next tile before current-tile computation finishes.
- The unresolved bottleneck is reduction structure, access representation, working-set size, grid scheduling, or transfer concurrency rather than per-program overlap.
- Generated IR and high-confidence mapped intervals already show adequate coordination with no measured remaining gap.
- Actual generated buffering, live ranges, or spills make the candidate fail to fit or run slower.

## Signals

### Code

- A regular tiled loop repeatedly loads independent A/B tiles and computes on them.
- Source load-then-compute order does not prove synchronous target execution.
- A carried tile or source-written prefetch changes source lifetimes, but does not prove asynchronous transfer.

### Profile

- Engine idle regions, Task Wait, or transfer/compute imbalance can motivate exploration.
- Mapped MTE and Cube/Vector intervals from the same program and shape provide high-confidence attribution and acceptance evidence.
- Aggregate engine ratios alone do not establish temporal overlap.

### IR

- Inspect generated buffer count, MTE-to-Cube/Vector set/wait handshakes, allocation, live ranges, and spills.
- `hivm.multi_buffer` or equivalent metadata shows generated coordination, not by itself timed overlap or speedup.
- Compare control and candidate IR for an actual scheduling change instead of inferring execution from source syntax.

## Method

Confirm the fit first: freeze math, dtype, masks, logical tile, grid, stages,
and work; record iteration counts for representative shapes; capture baseline
benchmarks, target IR, compiler allocation, and available profile evidence.
Inspect generated buffer depth, handshakes, live ranges, and spills before
changing source structure.

An ordinary loop and a textual prefetch may lower to the same target
schedule:

```text
ordinary: load(tile); compute(tile)
prefetch: load(next); compute(current); carry(next)
```

The compiler may already multibuffer the ordinary form, schedule both forms
identically, or reject the longer carried live ranges. Comments such as
`async` and `prefetch` are hypotheses, not execution evidence.

The optimization core is to expose a regular streaming recurrence to the
compiler (Candidate 1), and only if evidence still shows a gap to test one
guarded manual-carry schedule as an ablation (Candidate 2). Compare generated
scheduling and allocation between control and candidate; use mapped intervals
and repeated benchmarks for attribution and acceptance. Stop on identical
lowering, a candidate that no longer fits or spills, or no repeated end-to-end
latency improvement.

### Candidate: Regular streaming control

Use block pointers only when the current pointer recurrence prevents the
compiler from seeing regular streaming. Do not rewrite an existing regular
IR-generated stream merely to introduce block pointers.

```diff
- a = tl.load(a_base + offsets_for(k), mask=mask_for(k))
+ a = tl.load(a_ptr, boundary_check=(0, 1))
  acc = tl.dot(a, b, acc)
+ a_ptr = tl.advance(a_ptr, (0, BLOCK_K))
```

This control exposes a regular recurrence for compiler analysis. Any benefit
from transfer shape or access dimensionality belongs to `block-pointer-tiles`
and must be attributed separately.

### Candidate: Manual carry as a scheduling ablation

This is not a preferred implementation template. Behind a branch where
`num_k_tiles >= 1`, use one minimal prologue/steady-state/epilogue candidate
to test whether source lifetimes alter generated scheduling:

```diff
- for _ in range(num_k_tiles):
-     a = tl.load(a_ptr)
-     b = tl.load(b_ptr)
-     acc = tl.dot(a, b, acc)
-     a_ptr = tl.advance(a_ptr, (0, BLOCK_K))
-     b_ptr = tl.advance(b_ptr, (BLOCK_K, 0))
+ # guarded by num_k_tiles >= 1
+ a_current = tl.load(a_ptr)                         # prologue
+ b_current = tl.load(b_ptr)
+ for _ in range(1, num_k_tiles):                   # steady state
+     a_ptr = tl.advance(a_ptr, (0, BLOCK_K))
+     b_ptr = tl.advance(b_ptr, (BLOCK_K, 0))
+     a_next = tl.load(a_ptr)
+     b_next = tl.load(b_ptr)
+     acc = tl.dot(a_current, b_current, acc)
+     a_current, b_current = a_next, b_next
+ acc = tl.dot(a_current, b_current, acc)            # epilogue
```

One tile is handled by prologue plus epilogue. Real code must provide the
operator's correct zero-tile fallback and preserve masking or boundary checks
for a partial final tile. `tl.load` is not claimed to be asynchronous;
identical lowering is a useful negative result.

### UB and fit accounting

Use compiler-reported usable UB for the compiled target and actual generated
buffer depth. Account for A/B tiles, accumulators, masks, boundary values,
conversions, current/next carried values, compiler temporaries, and spills.

Do not hardcode nominal UB capacity, assume exactly two buffers, or estimate
footprint as `2 * tile`. Manual carry can extend lifetimes on top of
generated buffering. Reject candidates that fail memory planning, spill
substantially, or require an untracked tile change.

### Discipline

Keep a manual schedule only when the target IR, fit, correctness, and
repeated end-to-end timing show an attributable improvement over the
regular-streaming control. Verify one, two, and many iterations, including
the zero-tile fallback where the operator supports it and a partial final
tile.

## Related Patterns

- [block-pointer-tiles](../techniques/memory_access_optimization.md): owns transfer-shape and access-dimensionality effects.
- [dot-matmul-rewrite](./dot_matmul_rewrite.md): owns conversion to regular tiled `tl.dot` structure.
- [tile-footprint-fitting](../techniques/tiling.md): owns tile footprint and usable-UB fit.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): separates scheduling effects from tile or fit changes.
- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): separates per-program overlap from grid and transfer-concurrency effects.
- [现有知识：multibuffer=True 与手动双缓冲实操](../operator_optimization/multibuffer_and_double_buffering.md)

## What To Verify After Applying

- Correct values, dtype, masks, zero-tile behavior where the operator supports it, and partial-tail handling for one, two, and many iterations.
- Control and candidate perform identical logical work with the same tile, grid, stages, and comparison conditions.
- Target IR shows the claimed change in schedule, buffer count, handshakes, and live ranges.
- Compiler-reported usable UB includes generated/manual buffers, accumulators, temporaries, and spills without nominal-capacity shortcuts.
- Mapped MTE and Cube/Vector intervals support the accepted overlap attribution.
- Repeated canonical benchmarks show an attributable improvement over the regular-streaming control.
