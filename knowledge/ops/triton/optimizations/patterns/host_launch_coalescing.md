---
type: Optimization
title: Host Launch Coalescing
description: 把 Python/wrapper 循环对同一小 kernel 的重复 launch 合并为一次 device grid，由 program 自行解码段身份。
tags: [task.optimization, topic.parallelism, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/host-launch-coalescing.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Host Launch Coalescing

## Summary

Replace repeated Python or wrapper launches of the same small kernel across independent logical segments with one device grid whose programs decode segment identity. The mechanism is fewer host/kernel launches and a larger submitted work set, paid for by device metadata loads, identity decode, and control.

## Use When

A Python or wrapper loop launches the same small kernel once per batch item,
head, sequence bucket, or ragged segment. A typical example:

```python
for segment in range(num_segments):
    kernel[(grid_for_segment,)](x + offsets[segment], out + offsets[segment])
```

This is worth merging when each launch is so short that host dispatch and
kernel-launch overhead is a visible share of total latency. It is possible
when the segments are independent: their outputs can go to disjoint regions
of one launch's output, and their per-segment metadata (lengths, offsets,
strides) can be passed to the device as arrays.

The merged form replaces the loop with one device launch whose programs
decode their own segment identity, removing the repeated dispatch and launch
overhead.

## Avoid When

- The repeated calls invoke different algorithms, dtypes, compile-time configurations, or synchronization dependencies that cannot share one kernel contract.
- Coalescing would create overlapping output ownership or require cross-segment ordering.
- One launch already contains the complete logical work set; use `engine-aware-grid-scheduling` for mapping inside that launch.
- Metadata and control cost dominates because there are very few launches or each launch already performs substantial work.

## Signals

### Host

- Python iterates over batch, heads, sequence buckets, or ragged records and slices pointers before every call.
- A wrapper constructs many grids for the same compiled kernel during one operator invocation.

### Code

- The kernel receives one segment's base pointer or length, even though all segments use identical elementwise or reduction logic.
- Outputs are naturally partitioned by a logical segment ID.
- Ragged offsets or lengths already exist on the host and could be passed as arrays.

### Profile

- The timeline contains many short instances of the same kernel with gaps or launch overhead between them.
- Per-kernel latency is small, but their count makes total-operation latency significant.
- Kernel-only timing looks acceptable while wrapper or end-to-end operator timing remains high.

### IR

- IR is useful for checking the added metadata/decode/control cost, but it cannot establish the removed host launch cost. Attribute success with total-operation timing and launch count.

## Method

Confirm the fit first: the repeated launches run the same compiled kernel over independent segments, and total-operation timing — not kernel-only timing — shows host dispatch and launch gaps costing a visible share. Record launch count and per-launch work as the baseline.

The optimization core is to replace the per-segment host loop with one device launch whose grid covers every logical item, with each program decoding its segment identity from device-visible metadata. Apply the rules below in order; the first two define the candidate, the last two keep it cheap and correct.

### Rule: Define logical items and prove disjoint output ownership

Define one logical item before rewriting, and record how input/output offsets, lengths, strides, and optional head identity are decoded for every item. For example, logical item `(segment, tile)` may own:

```text
[out_offsets[segment] + tile_start,
 min(out_offsets[segment] + tile_end, out_offsets[segment + 1]))
```

No two logical items may write the same output element unless the original semantics provide an explicit atomic or reduction protocol.

### Rule: Move the repeated host loop into one launch

```diff
- for segment in range(num_segments):
-     length = offsets[segment + 1] - offsets[segment]
-     kernel[(ceil_div(length, BLOCK),)](
-         x + offsets[segment], out + offsets[segment], length,
-     )
+ tiles_per_segment = [ceil_div(length, BLOCK) for length in lengths]
+ tile_prefix = exclusive_prefix_sum(tiles_per_segment)
+ kernel[(tile_prefix[-1],)](
+     x, out, offsets, tile_prefix, num_segments,
+ )
```

The device grid now carries logical identity, so the kernel decodes a global program ID into a segment and a local tile:

```python
pid = tl.program_id(0)
segment = locate_segment(tile_prefix, pid)
local_tile = pid - tl.load(tile_prefix + segment)
start = tl.load(offsets + segment)
end = tl.load(offsets + segment + 1)
offs = start + local_tile * BLOCK + tl.arange(0, BLOCK)
mask = offs < end
vals = tl.load(x + offs, mask=mask, other=0.0)
tl.store(out + offs, transform(vals), mask=mask)
```

### Rule: Match identity decode cost to the segment distribution

A direct lookup table suits many tiny uneven segments; arithmetic decode suits equal segment grids; a compact prefix search suits a small number of ragged segments. Benchmark the metadata construction too when it occurs inside the measured operator.

### Rule: Keep empty, short, and uneven segments correct

- Empty segments contribute zero logical tiles and preserve their empty output range.
- Short segments contribute one partially active tile with masked lanes.
- Uneven segments derive tile counts from each segment's real length; do not allocate work based only on the maximum length unless the padding cost is measured and accepted.
- Program-level no-work, such as a decoded item outside the logical count, can early-return.
- Partial lanes and tail elements remain in an active program and use masks so loads and stores stay in bounds.

Discipline: build the smallest coalesced candidate that changes only launch count — keep kernel math, tile size, dtype, and output semantics fixed. Measure metadata preparation, metadata loads, decode/control instructions, submitted program count, and total-operation latency on a shape set spanning one/few segments, many short segments, uneven ragged segments, and longer segments. If one coalesced launch is established but program mapping remains inefficient, explore axis order, program batches, persistence, or thin-axis serialization with `engine-aware-grid-scheduling` as a separate experiment.

## Related Patterns

- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): map logical work into program order, program batches, or persistent loops after one launch defines the work set.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): increase adjacent row ownership within one program when row-wise programs are too thin.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): represent an owned regular multidimensional transfer independently of launch coalescing.
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): compare coalescing with removing a wrapper launch through semantically valid fusion.

## What To Verify After Applying

- Parent and candidate perform the same logical operations with identical dtype, masks, and numerical semantics.
- Every logical item has complete, disjoint output ownership; ragged offsets cannot produce overlap or out-of-bounds access.
- Empty, short, uneven, and tail segments match the reference.
- Launch count decreases as intended and the submitted work set is large enough to explain the mechanism.
- Total-operation timing includes host dispatch and any metadata construction; kernel-only latency is reported separately.
- Metadata traffic, decode/control cost, program count, and representative shape results are recorded, including regressions where launch savings do not repay device overhead.
