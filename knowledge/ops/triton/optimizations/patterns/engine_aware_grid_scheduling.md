---
type: Optimization
title: Engine-Aware Grid Scheduling
description: 把单次 launch 内的逻辑工作映射为 program 顺序、紧凑活跃任务域、program batch、persistent 步进循环或有界串行轴。
tags: [task.optimization, topic.parallelism, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/engine-aware-grid-scheduling.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Engine-Aware Grid Scheduling

## Summary

Map logical work already contained in one device launch into program order, a compact live-task domain, program batches, persistent stride loops, or a bounded serialized axis. Keep work and tile math fixed for the first comparison, and retain a mapping only when its scheduling, decoder, compiler-allocation, or DMA-concurrency effect is separately measured.

## Use When

A kernel already covers all of its logical work in one launch — if a host
loop launches it once per segment, apply `host-launch-coalescing` first — and
you suspect the program-to-core mapping wastes resources while the per-tile
work itself is fine.

One or more of these situations holds:

- **Heterogeneous programs**: programs differ in loop length, memory region,
  or Cube/Vector mix, so which programs share a batch matters.
- **Padded-grid no-ops**: a rectangular grid padded to the maximum submits
  many programs that only decode metadata and return early, because their
  tiles fall outside ragged segment lengths.
- **Batch-boundary count**: the logical program count sits close to a
  program-batch boundary or leaves the last batch mostly idle.
- **Thin programs**: per-program setup dominates, or a small independent grid
  axis could move inside the program.

Profile or IR confirms the mapping matters: latency shifts when one program
batch finishes and the next starts, or a Vector-heavy and a Cube-heavy kernel
respond oppositely to the same axis order.

## Signals

### Code

- Grid axes encode batch/head, row group, sequence position, or recurrence position, but the mapping does not explain which programs execute together.
- A host grid is changed together with tile dimensions, obscuring scheduling versus tiling effects.
- A global-maximum grid decodes segment-local lengths only after launch, even though a prefix of live tile counts could define the submitted tasks directly.
- A persistent loop replaces an ordinary logical grid and may serialize transfers that were concurrent.
- A thin independent axis creates many tiny programs, or moving it into a loop would make each program much longer.

### Profile

- Latency changes at a program-batch boundary although per-logical-item tile work is unchanged.
- Programs issued in the same batch have different recurrence lengths or locality.
- A material fraction of submitted programs performs only metadata decode and an early return because its tile is outside a segment-local length.
- Forward/vector and backward/Cube paths move in opposite directions under the same axis order.
- MTE/DMA concurrency changes after reducing physical programs or lengthening each program.

### IR

- The same tile receives different buffer lifetimes or allocation under ordinary and persistent mapping.
- Serial-axis candidates enlarge generated code or expose unrolled repeated bodies.
- A compact task decoder introduces scalar searches, division/modulo chains, or metadata loads whose cost may offset the programs it removes.
- Use IR to explain mapping and allocation changes, not to infer timed overlap from ratios alone.

## Establish Physical Capacity

Obtain candidate physical capacity from trustworthy target, compiler, launch-configuration, or profiler evidence, or use bounded experiments around capacities justified by that evidence. `torch.npu.device_count()` reports the number of NPU devices, not the number of Cube or Vector cores. Do not substitute a universal fallback capacity or prescribe one capacity across targets and engine mixes.

Treat physical capacity as a reference for constructing grid candidates, not as a required launch size. When total logical work is much larger, test a few bounded multiples of capacity to balance per-program overhead against scheduling and transfer concurrency.

Record whether capacity refers to the relevant Cube, Vector, mixed, or launch-resource limit. If exact capacity is unavailable, label it as an experimental candidate and compare a small bounded set rather than presenting it as hardware fact.

## Method

Confirm the fit first: all logical work lives in one launch, the hypothesis
concerns how programs map to physical execution, and dtype, masks, logical
item count, output ownership, and tile dimensions stay frozen as the control
baseline. State the target: batch fill, work variance, locality, program
thinness, allocation, or transfer concurrency. Decode the current grid and
calculate logical programs, candidate batch counts, and last-batch fill for each
justified capacity:

```python
batches = ceil_div(logical_programs, physical_capacity)
last_batch_fill = logical_programs - physical_capacity * ((logical_programs - 1) // physical_capacity)
```

The optimization core is to change the mapping — program order, physical
program count, a serialized axis, or a compacted task domain — while holding
tile work fixed, keeping a candidate only when its effect is separately
measured. Use profile evidence to identify whether the path is Cube-heavy,
Vector-heavy, transfer-heavy, or mixed; a lower batch count without lower
canonical latency is not a win. Preserve complete logical coverage and
disjoint outputs, run correctness before timing, and shape-gate mappings when
engines or shapes choose differently.

### Candidate: Change axis order

Freeze logical work and swap only program order:

```diff
- grid = (num_m_groups, batch_heads)
- m_group = tl.program_id(0)
- bh = tl.program_id(1)
+ grid = (batch_heads, num_m_groups)
+ bh = tl.program_id(0)
+ m_group = tl.program_id(1)
  process_tile(bh, m_group, BLOCK_M=BLOCK_M, BLOCK_N=BLOCK_N)
```

Test this as an isolated mapping change when batch composition or locality is the hypothesis. It may help one dominant engine and hurt another.

### Candidate: Use a persistent physical-program stride loop

Compare an ordinary grid with a bounded physical-program-count candidate while preserving each logical item's ownership:

```diff
- grid = (total_logical,)
- logical = tl.program_id(0)
- process(decode(logical))
+ program_count = min(total_logical, GRID_MULTIPLIER * physical_capacity)
+ grid = (program_count,)
+ logical = tl.program_id(0)
+ while logical < total_logical:
+     process(decode(logical))
+     logical += program_count
```

First compare ordinary and persistent mappings at the same tile and logical work. This equal-tile control isolates scheduling and loop overhead. Test a small bounded multiplier set: more programs add per-program setup and dispatch overhead but may preserve useful concurrency, while fewer programs reduce overhead but serialize more work. Multipliers are experiment points, not fixed rules. If persistence changes compiler buffer lifetime or makes a previously illegal larger tile legal, test that larger tile only as a follow-up. Report three mechanisms independently: equal-tile scheduling, compiler buffer-lifetime/legal-tile change, and DMA-concurrency change.

Aggressively reducing the number of programs can regress because longer
programs change work balance, compiler allocation, or DMA concurrency.

### Candidate: Serialize a thin independent grid axis

When `batch_heads` is small and each program is thin, test moving that independent axis inside the program:

```diff
- grid = (chunks, batch_heads)
- chunk = tl.program_id(0)
- bh = tl.program_id(1)
- process(chunk, bh)
+ grid = (chunks,)
+ chunk = tl.program_id(0)
+ for bh in range(batch_heads):
+     process(chunk, bh)
```

This trades parallelism for more work per program. It can produce longer programs, larger code or compile-time unrolling, and lower DMA concurrency. Test it only when the axis is small, outputs are disjoint, and the original programs are demonstrably thin; retain ordinary parallel execution for shapes where serialization underfills the device.

### Candidate: Compact a ragged rectangular grid into live tasks

After `ragged-tile-early-return` proves that whole-invalid tiles are
common and safely removable, test whether submitting only live tiles also
recovers meaningful launch, decode, or scheduling cost. Derive each segment's live
tile count from authoritative runtime metadata and define a bijection between a
compact task ID and its `(segment, independent axis, local tile)` owner. A
prefix table, bounded lookup, or other measured decoder may implement the
mapping; the representation is a design choice, not a fixed recipe.

Do not embed captured segment lengths, benchmark case identities, or a static
task table as the mapping contract. If a static specialization is justified,
its host guard must verify every runtime property that determines the task map,
including the relevant segment boundaries or lengths. Checking only a global
maximum, tensor shape, or broad regime is insufficient. Keep the rectangular
mapping as the fallback for unseen or mismatched metadata.

Compare rectangular and compact mappings with the same tile body, tile shape,
math, masks, and output ownership. Account for host prefix construction,
metadata transfers, per-program decode, changed program count, and batch
composition. A compact grid can regress when decode is expensive or when the
larger rectangular population provided useful concurrency, so retain it only
for causally defined regimes with a complete-operation win.

## Related Patterns

- [host-launch-coalescing](./host_launch_coalescing.md): form one device launch from repeated wrapper launches before tuning its internal mapping.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): change adjacent-row ownership and work per program; it does not require persistence.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): choose regular transfer representation independently from grid ownership and mapping.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): isolate a compiler allocation or larger-tile effect enabled by persistence.
- [l2-stripe-capacity-tile-widening](./l2_stripe_capacity_tile_widening.md): change the tile aspect ratio when the bottleneck is L2 stripe capacity rather than program mapping; this card keeps tile math fixed, that card changes it.
- [ragged-tile-early-return](./ragged_tile_early_return.md): first remove the body of whole-invalid programs without changing the launch mapping; compact the grid only when the residual submitted-program cost remains material.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): recalculate logical work and variance after removing invisible attention regions.
- [现有知识：Core 映射策略](../techniques/core_mapping.md)
- [现有知识：Persistent Kernel 与 grid-stride](../techniques/persistent_kernels.md)

## What To Verify After Applying

- Parent and candidate cover identical logical items, tile shapes, dtypes, masks, and output regions for the equal-tile control.
- Record the evidence or experiment defining physical capacity; do not treat device count as core count.
- Record logical program count, program batches, final-batch fill, work variance, locality target, and dominant engine by shape.
- For persistent variants, test a small bounded program-count set and report equal-tile scheduling, compiler buffer allocation or legal-tile change, and MTE/DMA concurrency separately.
- For serialized axes, test several axis sizes and record lost parallelism, program duration, code size/unrolling, and DMA concurrency.
- For compact ragged mappings, verify that runtime-derived task ranges cover every live tile exactly once, that mismatched metadata reaches the rectangular fallback, and that no captured length table silently defines correctness.
- Accept by correctness and canonical latency; batch arithmetic, allocation changes, or profiler ratios alone do not prove a benefit.
