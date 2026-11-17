---
type: Optimization
title: Tile 工作集适配
description: 调整分块和存活中间量，使每个 program 的工作集落在可用片上容量内。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/tile-footprint-fitting.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Tile Footprint Fitting

## Summary

Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.

## Use When

A kernel processes its data in one large flat block and keeps several tensor
tiles or intermediates live at the same time, so the per-program working set
approaches or exceeds UB capacity:

```python
offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)  # one large flat block
a = tl.load(x + offsets, mask=mask)
b = tl.load(y + offsets, mask=mask)
c = tl.load(z + offsets, mask=mask)                    # several tiles live at once
result = compute(a, b, c)                              # UB overflow risk here
```

The compiler-reported UB allocation or a runtime failure confirms the
overflow. Growing `BLOCK_SIZE` makes the failure or the pressure worse. The
kernel's overall structure is otherwise reasonable — the problem is
per-program memory footprint, not the need for a different kernel shape.

Splitting the block into sub-blocks processed in sequence keeps only one
sub-block live at a time, so the tile fits UB.

## Avoid When

1. **Small BLOCK_SIZE** with no significant memory pressure.
2. **Simple single-tensor operations** where UB usage is minimal.
3. **Sub-blocking already present** in the kernel.
4. **Structure is the real problem** — a manual reduction or matmul that should first become a regular tiled `tl.dot` loop; use [`dot-matmul-rewrite`](dot_matmul_rewrite.md) instead.

## Signals

### Code

- Large `BLOCK_SIZE` values with multiple tensor loads or heavy intermediates live per program.
- Runtime failures or memory access violations appear when block sizes increase on NPU.

## Method

Confirm the fit first: the compiler-reported UB allocation or a runtime error
must show the per-program working set exceeding capacity, and the kernel must
not have a separate structural problem (see Avoid When).

The optimization core is two-level blocking: keep the main `BLOCK_SIZE` for
task scheduling and coreDim compliance, and introduce a smaller
`BLOCK_SIZE_SUB` so an inner loop processes the block in batches. Peak live
data then follows the sub-block size instead of the full block.

### Rule: Split one large block into an inner sub-block loop

```diff
- def kernel(..., BLOCK_SIZE: tl.constexpr):
-     offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
-     mask = offsets < N
-     a = tl.load(x + offsets, mask=mask)
-     b = tl.load(y + offsets, mask=mask)
-     tl.store(out + offsets, compute(a, b), mask=mask)
+ def kernel(..., BLOCK_SIZE: tl.constexpr, BLOCK_SIZE_SUB: tl.constexpr):
+     for sub in range(tl.cdiv(BLOCK_SIZE, BLOCK_SIZE_SUB)):
+         local_offsets = sub * BLOCK_SIZE_SUB + tl.arange(0, BLOCK_SIZE_SUB)
+         offsets = pid * BLOCK_SIZE + local_offsets
+         mask = (local_offsets < BLOCK_SIZE) & (offsets < N)
+         a = tl.load(x + offsets, mask=mask)
+         b = tl.load(y + offsets, mask=mask)
+         tl.store(out + offsets, compute(a, b), mask=mask)
```

Update the host launch to pass both block sizes. Choose `BLOCK_SIZE` so the
grid stays within coreDim limits, and let the inner loop control the UB
footprint. The local bound prevents the last sub-block from entering the
next program's block when the sizes are not divisible; the global bound
handles the tensor tail. For `N=4096`, `BLOCK_SIZE=1536`, and
`BLOCK_SIZE_SUB=1024`, program ownership remains `[0,1536)`, `[1536,3072)`,
and `[3072,4096)`, with every valid address visited once. These are address
arithmetic checks, not a claim that every backend accepts these tile sizes.

### Rule: Size the sub-block against UB, performance, and alignment

- UB-safe: 1024–2048 elements for simple element-wise chains, 512–1024 for multi-tensor operations, 256–512 for complex reductions.
- Performance-aware: large enough that loop and indexing overhead stays small.
- Alignment-aware: compatible with the 32-byte alignment requirement and the vector width (typically 128/256 elements).

### Rule: Choose the initial tile width from reuse and layout, not habit

For the first structurally valid tiled candidate, avoid a habitual narrow
width such as 64 on a sufficiently large contiguous or low-stride axis; 128
is not a default either. Choose which axis to widen from operation reuse and
work ownership: a non-tail ownership axis may be best when widening it
reduces program count, repeated full traversal, or redundant loads. Choose
the width from physical stride and layout, real axis length, operation
structure, and UB/resource limits — not from a logical dimension name alone.

After profiling, prioritize the axis that directly reduces the measured
bottleneck. Shrink, enlarge, or redirect the tile based on compile and
correctness results, profiler evidence, occupancy and program-batch behavior, padding,
layout effects, UB pressure, and repeated benchmark measurements. If a
candidate does not compile or is resource-heavy, fall back to the widest
structurally valid narrower candidate supported by that evidence.

### Rule: Amortize fixed per-program work with a strided loop when UB caps the tile

Small compute tiles fix UB overflow but multiply the program count; when
every program re-loads the same invariant operands (broadcast rows, weights,
shared tiles), that fixed cost is paid once per program. Keep the small tile
that satisfies UB, but let one program stride over several tiles of the same
logical row:

```python
tile = tl.program_id(2)
while tile < NBLK:                      # strided loop, NOT nested static_range
    ... process tile (dot + per-tile selection) ...
    tile += tl.num_programs(2)
```

- Implement the stride as a `while` loop on the program id. A nested `tl.static_range` unroll can make generated code much larger; compare compile time, compile success, and runtime before choosing either form.
- This differs from the sub-block loop above: sub-blocking fits UB inside one logical block; striding amortizes fixed per-program work after UB already forced the tile small.
- Probe first: when per-program invariant loads are negligible, the strided form can be several times worse than independent programs because work ownership and scheduling change.
- Structural changes from other patterns (for example [`int8-dot-int32-accumulator`](int8_dot_int32_accumulator.md), or partial-state splits from [`reduction-axis-split-combine`](reduction_axis_split_combine.md)) change UB pressure — re-run this check after applying them.

Discipline note: apply one rule at a time and re-measure after each. Keep a
candidate only if the compiler-reported UB allocation drops and end-to-end
latency does not regress.

## What To Verify After Applying

- Verify the chosen `BLOCK_SIZE_SUB` fits the operation type and keeps the working set UB-safe.
- Verify the inner sub-block loop actually reduced peak live data instead of only adding loop overhead.
- Verify both kernel signature and host launch code pass the new block-size parameters consistently.

## Expected Performance Impact

**Memory Usage:**
- Sub-blocking can reduce the tile-dependent part of the UB footprint and may make a larger logical problem fit. The actual reduction depends on live inputs, masks, alignment, compiler buffering, and spills; verify compiler-reported allocation.

**Performance Trade-offs:**
- **Pros**: May make an otherwise oversized tile compile.
- **Cons**: Adds loop and indexing work and may repeat invariant loads.
- **Verification**: Compare peak allocation, compile result, and end-to-end latency against the unsplit version.

## Related Patterns

- [`dot-matmul-rewrite`](dot_matmul_rewrite.md): use it first when the real problem is that a manual reduction should become a tiled matmul structure at all.
- [`software-pipeline`](software_pipeline.md): combine it only after the footprint already fits UB, because pipelining deliberately keeps multiple tiles live.
- [`engine-aware-grid-scheduling`](engine_aware_grid_scheduling.md): separate tile math from physical program mapping and traversal.
- [`l2-stripe-capacity-tile-widening`](l2_stripe_capacity_tile_widening.md): size tiles against L2 stripe capacity when the streamed operand falls off a throughput cliff; this card sizes against UB capacity.
- [`large-tile-fit-enabling`](large_tile_fit_enabling.md): isolate a tile from the live-range or precision change that makes it fit.
- [`intermediate-layout-copy-deletion`](intermediate_layout_copy_deletion.md): compare regular and consumer-native epilogues independently from the contraction tile.

**Caution — reference tile tuples**: a tile size copied from a faster
reference implementation is entangled with that implementation's buffering,
traversal, physical mapping, accumulator split, and epilogue. Transplant
components one at a time as separate experiments instead of copying the bare
M/N/K tuple, and test geometry on a regular single-destination output before
a segmented epilogue — a tile that helps a regular output can regress a
segmented one.
