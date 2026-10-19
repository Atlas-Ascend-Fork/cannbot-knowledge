---
type: Optimization
title: Kernel Fusion And Value Placement
description: 当可共享计算或省去中间张量写回时合并算子；当分开能保住更快路径或边界时保持独立，并决定值的驻留位置。
tags: [task.optimization, topic.compute.composite, topic.data_movement.data_copy]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/kernel-fusion-and-value-placement.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Kernel Fusion And Value Placement

## Summary

Combine operations when they can share computation or avoid writing an intermediate tensor to memory. Keep separate kernels when that permits a faster schedule. Distinguish computational fusion from launch coalescing and compiler-internal fusion, and choose each boundary from semantic validity, schedule compatibility, and measured total-call behavior—not from kernel count or compiler precedent alone.

## Use When

One operator call runs as several back-to-back kernels or torch operations
(copies, casts, allocations), and a large intermediate tensor is written to
memory by one launch and read back by the next. A typical example — an
attention call split into three kernels:

```python
scores = qk_kernel[grid](q, k)        # large intermediate written to memory
probs = softmax_kernel[grid](scores)  # read back, then written again
out = pv_kernel[grid](probs, v)
```

The same waste shows up in other shapes:

- **Sibling or fan-out launches**: several launches reload the same inputs.
- **Repeated dominant work**: multiple launches repeat the same dominant
  matmul, reduction, or expensive elementwise chain over the same tiles.
- **Glue ops between kernels**: torch-level copies, casts, or allocations
  sitting between otherwise related computations.

The card guides two decisions from here: which of these launches to fuse into
one kernel, and where each boundary value lives (forwarded on-chip, written
out, or recomputed).

## Avoid When

- The boundary sits outside the profiled path and cannot change the reported metric.
- A semantic, ownership, synchronization, mutation, alias, layout, or backend requirement already makes the merge invalid.

## Why Group Work

Grouping compatible work can:

- eliminate intermediate GM/HBM writes, reads, allocations, and workspace;
- remove launch, dispatch, and wrapper overhead;
- improve locality or reuse by placing values near their consumers;
- permit a joint schedule unavailable to separately compiled work.

These are possible benefits, not a rule to fuse. Grouping can also force incompatible iteration spaces into one schedule, repeat producer work, lengthen live ranges, reduce occupancy or parallelism, constrain tiles, or lose a specialized library or engine. A graph finds candidate relationships and hard constraints; domain, access, ownership, and schedule compatibility determine whether grouping is plausible, and target measurements decide whether it is profitable.

Computational fusion is different from launch coalescing. Launch coalescing changes the submitted program set while retaining the original work; computational fusion shares a tile's dominant computation and removes duplicate work. Compiler or HFusion-internal fusion is a lowering result and does not by itself establish either source-level property.

## Method

Confirm the fit first: the profiled call must contain more than one launch or framework operation, and the profile must show intermediate traffic, allocations, or launch overhead contributing materially to total latency. A genuinely single-kernel call with nothing relevant between launches skips this card and proceeds directly to kernel-local optimization.

The optimization core is two decisions made together: **kernel fusion** —
which compatible launches merge into one kernel — and **value placement** —
where each boundary value lives (forwarded on-chip, written out as an output
or byproduct, or recomputed where consumed). Decide both from evidence:
compile, correctness, matched-cost, or benchmark evidence; risk adjectives
alone do not justify a rejection. Evaluate these structural candidates before
kernel-local, refinement, or autotune patterns. When dominant work repeats
across launches, include at least one shared-computation candidate and prefer
preserving exclusive ownership for the largest or most expensive outputs.

### Rule: Inventory the profiled dataflow before choosing either decision

Scan every multi-component profiled call before selecting kernel-local patterns. A simple linear chain needs only an ordered inventory of components, boundary values, and metric inclusion. Reconstruct a lightweight graph only when dependencies, fan-out, reconvergence, external users, or nontrivial barriers require one; matching launch grids or tensor shapes is not evidence of compatibility.

Identify real device boundaries from `kernel[grid](...)` launch sites and profiler operations, not from the number of `@triton.jit` helper definitions. Record only the facts the candidate needs:

- iteration, ownership, and tile domains, plus indexing and access maps;
- input, accumulator, and output dtypes, including observable rounding points;
- layouts, aliasing, mutation, synchronization, and external uses;
- intermediate bytes, allocation cost, load/store and recompute multiplicity, and actual reuse;
- backend, library, or execution-engine placement and support;
- whether launch, allocation, traffic, and component latency are included in the reported metric.

### Fusion: enumerate the grouping families, including retaining the boundary

List plausible choices without assuming that grouping helps:

- **Vertical producer-consumer grouping:** move compatible producer or epilogue work into a consumer schedule.
- **Horizontal sibling grouping:** combine independent nodes that share inputs or coordinates when one schedule preserves their ownership and semantics.
- **Multi-output grouping:** preserve fan-out by producing all externally required outputs from shared compatible work.
- **Tile-and-fuse / compute-at:** produce tiles in consumer ownership, accepting controlled recomputation when profitable.
- **Shared-computation fusion:** keep one program domain for the dominant tile computation while assigning each output to local, written-out, or atomic accumulation according to ownership.
- **Retained boundaries:** keep separately tuned kernels, written-out values, framework operations, or specialized library calls.

Grouping order can matter: accepting one group may make another invalid or unprofitable, so reconsider neighboring candidates after each grouping decision.

### Fusion: reject early when a candidate cannot preserve semantics

Reject a candidate before benchmarking when it cannot preserve:

- acyclic dependencies and a valid execution order;
- every external use, including fan-out and required multi-output behavior;
- compatible indexing, iteration domains, access maps, and program ownership;
- required synchronization and cross-program communication boundaries;
- dtype, rounding, layout, alias, mutation, and observable value semantics;
- backend lowering, supported operations, and library or engine requirements.

In particular, a Triton kernel cannot pass a GM intermediate between its own programs without a synchronization scheme the target supports. Never describe a merged kernel as storing an intermediate for unsynchronized cross-program consumption inside one launch; keep the launch boundary, change ownership or placement, or rule the variant out.

### Fusion: weigh saved traffic against recompute and resource cost

Savings can include launches, dispatch, allocations, intermediate writes and reads, redundant input loads, and producer work already available as a byproduct. Added costs can include recomputation multiplied across consumer tiles, longer live ranges, UB/register pressure, spills, occupancy or parallelism loss, tighter tile restrictions, extra outputs and stores, synchronization, and loss of a better library or execution engine.

Estimate recompute from ownership, not from graph shape:

```text
added_recompute_work =
    producer_work_per_consumer_execution
    × consumer_execution_count_after_placement
```

Derive the execution count from program ownership, tile and loop domains, fan-out, and reuse after placement: graph-level "one consumer" does not imply one execution. If placement recomputes only part of the producer, count that slice rather than the whole producer. Use this rough model to discard clearly poor candidates, then benchmark plausible ones. Do not reject a candidate that removes repeated dominant matmul, dot, reduction, or expensive elementwise work merely because atomic traffic, UB pressure, or compiler risk is possible; record concrete compile, correctness, matched historical, or quantified cost evidence first. Measured target hardware and compiler behavior are authoritative when estimates disagree.

### Value placement: choose where each boundary value lives

For each boundary value between operations, choose one placement:

- **Forward on-chip** — the consumer reads it directly from the producer's
  tile; only possible when the two sides are fused or share ownership.
- **Write out** — keep it as an output or byproduct at a launch boundary when
  other consumers need it, recompute is expensive, or the value must stay
  observable.
- **Recompute at the consumer** — when the value is cheap to rebuild and
  storing or forwarding it costs more than recomputation.

Placement is decidable without fusion: a producer can write the consumer's
layout directly, or a consumer can recompute, while both launches stay
separate.

### Discipline: change fusion and value placement one dimension at a time

Grouping (which compatible nodes share one schedule) and value placement (forward, write out, or recompute each boundary value) are independent questions. A variant that changes both cannot attribute its speedup or regression to either one. Hold one dimension constant in each comparison:

| Compare | Hold constant |
| --- | --- |
| separate versus merged launches | the same value placement |
| write-out versus forward versus recompute | the same grouping and schedule |

Test only variants that compile and preserve semantics. When a matched comparison cannot be constructed, record the ownership, synchronization, schedule, semantic, or backend reason.

Discipline note: verify semantics before interpreting performance, benchmark affected components and total-call latency across representative shapes including boundary tile counts, and keep the best evidence-backed choice for the target.

## Signals

### Code

- Separate nodes exchange large temporaries, share input coordinates, or compute values with multiple users.
- Consumer loops repeat producer work whose index domain excludes the consumer tile axis.
- Framework casts, copies, allocations, or library calls sit between otherwise related computations.

### Profile

- Intermediate traffic, allocations, or dispatch contribute materially to total latency.
- Removing traffic slows grouped work through resource pressure, repeated computation, or schedule restrictions.
- A specialized library, engine, or independently tuned schedule outperforms an apparently simpler merged implementation.

### IR

- Candidate grouping changes live ranges, UB/register pressure, spills, occupancy, synchronization, or compiler-accepted tile choices.
- Access maps or ownership domains do not align despite matching shapes or grids.
- Lowering changes dtype conversion, rounding, layout, or backend support across the boundary.

## Related Patterns

- [algebraic-optimization](./algebraic_optimization.md): compare a mathematical reassociation that deletes
  an intermediate with a fused implementation of the original dataflow; they
  can remove similar traffic through different mechanisms.

- [compute-once-share-via-gm](./compute_once_share_via_gm.md): the specific high-cost choice of writing values to GM after cheaper on-chip reuse, ownership, tiling, and forwarding alternatives fail.
- [dot-matmul-rewrite](./dot_matmul_rewrite.md): establish strong independently tuned kernel baselines.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): separate placement gains from tile changes.
- [intermediate-layout-copy-deletion](./intermediate_layout_copy_deletion.md): classify layout-only intermediates.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): reason about reuse and live ranges across programs.
- [common-input-projection-packing](./common_input_projection_packing.md): implement compatible horizontal affine siblings as a packed or co-scheduled common-input contraction, with controlled regular, segmented, and partial-output placements.
- [attention-online-softmax-fusion](./attention_online_softmax_fusion.md): implement a selected QK-softmax-value grouping as a tile-owned online recurrence.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): prune invisible and fully valid key tiles inside the recurrence when the visibility policy permits it.
- [l2-stripe-capacity-tile-widening](./l2_stripe_capacity_tile_widening.md): close a remaining L2-side gap by widening the reused-side tile before deciding to offload the stage.
- [现有知识：算子融合决策树](../techniques/operator_fusion.md)

## What To Verify After Applying

- Outputs and externally visible dtype, rounding, layout, alias, mutation, ownership, and multi-output behavior.
- Actual producer execution multiplicity, reuse, GM/HBM bytes, allocations, and extra output traffic.
- Compiler-reported accepted tiles, UB/register pressure, spills, occupancy, parallelism, and engine placement.
- Component and total-call latency across representative shapes, including launch, framework, allocation, and workspace costs.
