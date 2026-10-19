---
type: Optimization
title: Grid Flattening And UB Buffering Pattern
description: 把逻辑工作摊平到物理核并以更宽的 UB store 批量搬运小行传输，降低启动开销、提高单核工作密度。
tags: [task.optimization, topic.parallelism, topic.data_movement.data_copy]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/grid-flatten-and-ub-buffering.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Grid Flattening And UB Buffering Pattern

## Summary

Flatten logical work items onto physical cores and batch small row-wise memory transfers into wider UB stores to reduce launch overhead and improve per-core work density.

## Use When

The launched grid is much larger than the physical AICore or VectorCore count, so many tiny programs each handle only one or a few small rows. Work is partitioned by batch or sequence buckets with visible load imbalance, or a batch/head grid axis leaves each program too thin to cover its own launch and setup. Gather-like code whose destination rows are continuous but still stored one row at a time, and gradient-accumulation code that repeatedly loads consecutive source rows one at a time, have the same shape:

```python
pid = tl.program_id(0)               # grid >> physical core count
x = tl.load(src + pid * ROW + offs)  # each program moves one small row
tl.store(dst + pid * ROW + offs, x)
```

Flattening the grid onto the physical cores turns thousands of tiny programs
into one strided loop per core, and batching the row-wise transfers into
wider UB stores cuts per-program setup and transaction count.

## Method

Confirm the fit first: the program count must far exceed physical core count
(or per-program work must be too small to amortize launch), the kernel's
access semantics must be clear, and each physical program must still get
enough work to amortize an internal task loop. The optimization core is to
give each physical program a contiguous, evenly sized batch of logical work
items, then batch the small row-wise memory moves inside each program into
wider UB transfers.

### Rule: Flatten logical work items onto physical cores

Treat all independent logical work items as one continuous stream and split
that stream evenly across physical cores. When `logical_tasks > num_cores`,
launch `num_cores` programs and loop over logical tasks inside the kernel:

```python
pid = tl.program_id(0)
task_start = pid * TASKS_PER_CORE
offs = task_start + tl.arange(0, TASKS_PER_CORE)
mask = offs < TOTAL_TASKS
```

Compute `TASKS_PER_CORE` on the host and pass it as `tl.constexpr` when it
controls tensor shapes or loop bounds. Keep `NUM_TASKS` and `NUM_CORES` as
explicit constants so the compiler can simplify loop bounds. Prefer uniform
per-core loop structure and masks over early returns that create uneven
control flow. If the original grid is already near the physical core count,
the extra loop is overhead rather than a win.

### Rule: Collapse a thin batch/head axis into the program

For chunked attention or recurrence kernels, a grid like `(NT, B * HV)` can
create many small programs when each `(batch, head)` lane does modest work.
If the per-lane work is independent and writes disjoint output regions, and
`BH` is small enough that serializing the axis does not underutilize the
device, launch only over chunks and loop over `B * HV` inside each program:

```python
pid_t = tl.program_id(0)

for i_bh in range(BH):
    i_b = i_bh // HV
    i_h = i_bh % HV
    # Process one batch/head lane for this chunk.
```

Wrapper launch:

```python
kernel[(NT,)](..., BH=B * HV)
```

instead of:

```python
kernel[(NT, B * HV)](...)
```

This is a work-density variant of flattening, not a universal replacement
for parallel batch/head execution. Large compile-time `BH` values can
increase code size or make one program too long.

### Rule: Choose grid candidates from physical capacity and task kind

Obtain candidate physical capacity from trustworthy target metadata, compiler
or launch configuration, profiler evidence, or bounded experiments. Do not
use `torch.npu.device_count()` as a Cube or Vector core count: it reports the
number of NPU devices. Do not use one observed capacity or a fixed fallback
as a universal launch rule.

Treat capacity as a reference for constructing candidates, not as a required
launch size. When logical work is much larger than the relevant capacity,
compare a small bounded set of grids around that capacity or its justified
multiples, keeping work and tile math fixed so the first experiment measures
only mapping. Choose the initial candidate from the operator task kind:

- `cube`-like operators: use evidence for the relevant Cube capacity and verify that the kernel remains Cube-dominant.
- `vector`-like operators: use evidence for the relevant Vector capacity and retest after major tiling or buffering changes.
- `mix` operators: choose from the dominant bottleneck side, or test both engine-oriented candidates when the profile is ambiguous.

A faster result must be accepted by correctness and canonical latency, not by
capacity arithmetic alone.

### Rule: Batch continuous row writes into wider UB stores

After the grid rewrite gives each program several rows with continuous
destination addresses, stage a small group of rows in UB and issue a wider
2D store. Choose `SUB_BLOCK_SIZE` so the staged rows plus live compute
tensors fit UB. Do not use aggregate writes for genuinely scattered
destinations; gather and scatter have different address-continuity
requirements.

### Rule: Bulk-load continuous source rows into a UB slab

For row-wise reductions or gradient accumulation where several consecutive
source rows are loaded one at a time, load a small 2D slab into UB and
select rows from the slab. Keep a fallback path if row indices are not
continuous enough for a bulk read to be correct.

Apply the structural rewrite first and confirm correctness; only then tune
`TASKS_PER_CORE`, `BLOCK`, and `SUB_BLOCK_SIZE` with enough separation to
attribute the result. Record the capacity source, candidate grid, logical
program count, program-batch or final-batch behavior, and the shape gate for each
experiment.

## Risks

- Flattening can erase useful multidimensional locality if offsets are decoded poorly.
- Physical-grid loops can hurt small workloads.
- Serializing a batch/head axis can under-parallelize large `B * HV` or Cube-heavy workloads.
- UB staging can exceed UB capacity or reduce occupancy.
- Gather and scatter have different address-continuity requirements; do not reuse aggregate-write logic for scattered stores.

## What To Verify After Applying

- Record the physical core assumption and how it is discovered or passed.
- Validate edge cases where `TOTAL_TASKS` is not divisible by `NUM_CORES`.
- Benchmark small and large shapes if the operator supports both.
- If the win depends on row continuity, add that condition to the round summary.
- For batch/head-in-program loops, test several `B * HV` regimes and verify outputs are disjoint across the serial loop.

## Related Patterns

- [host-launch-coalescing](./host_launch_coalescing.md): combine repeated wrapper launches into one device launch first when those launches, not per-launch mapping, define the bottleneck.
- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): use when the main question is axis order, batch fill, persistence, or thin-axis serialization within one launch.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): widens row-wise work inside a program; complements this pattern, which flattens logical work onto physical cores and batches memory movement inside each core.
- [autotune](../operator_optimization/autotune.md): combine only after the structural rewrite is correct; tune `TASKS_PER_CORE`, `BLOCK`, and `SUB_BLOCK_SIZE` separately enough to explain the result.
- [现有知识：Persistent Kernel 与 grid-stride](../techniques/persistent_kernels.md)
