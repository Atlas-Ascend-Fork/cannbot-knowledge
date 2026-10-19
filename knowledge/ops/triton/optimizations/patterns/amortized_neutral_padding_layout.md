---
type: Optimization
title: Amortized Neutral-Padded Internal Layout
description: 为内部张量引入 tile 对齐的物理维度与中性填充值，把一次性 padding 代价摊销到多次消费中。
tags: [task.optimization, topic.tiling, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/amortized-neutral-padding-layout.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Amortized Neutral-Padded Internal Layout

## Summary

Introduce an internal tensor with tile-aligned physical extents and consumer-specific neutral values when one padding/preparation cost is amortized across repeated consumers. Keep logical extents as separate metadata so padding changes storage and lowering, not public semantics.

## Use When

One internal tensor's true length along a tiled axis is not tile-divisible
(e.g. 100 valid elements while tiles are 128), and several consumer kernels
or tiles read it repeatedly, with each consumer rebuilding the same boundary
handling — tail masks, pointer clamping, short transfers, or fill/select work
— on every read. The repeated boundary work outweighs a one-time preparation
pass, every consumer has a neutral value that makes padded lanes harmless to
its algebra (zero for dot/sum, the lower identity for max, the upper for
min), and padding to a tile-aligned physical extent unlocks a materially
better dot, reduction, vector-transfer, or block-pointer lowering on the
target.

## Avoid When

- The consumer still needs the same semantic mask, so padding removes no measured boundary work.
- Different consumers require incompatible neutral values or interpret padded coordinates as real positions.
- Extra padded compute, GM bytes, allocation, preparation, cache invalidation, or compilation outweigh the removed boundary path.
- The padded representation would become a public output, break alias or mutation semantics, or require a recovery copy for other users.
- Effective-extent tiling or an ordinary masked tail is already cheaper.

## Signals

### Code

- The same logical tail predicate, clamp, or `boundary_check` is rebuilt by many programs reading one internal tensor.
- An upstream producer already owns the destination allocation and could initialize aligned rows or columns while writing valid data.
- A contraction or reduction uses a legacy maximum block even though only its final logical extent is irregular.

### Profile

- Boundary fill/select, short DMA, scalar address generation, or tail launches recur across many consumer tiles.
- One preparation pass is small relative to the repeated consumer work, but total-operation measurements still include it.
- Naturally aligned shapes select a better lowering than otherwise similar irregular shapes.

### IR

- The padded candidate selects regular block transfers or legal Cube tiles without introducing compensating copies or excessive inactive work.

## Method

1. Record logical extents, proposed physical extents, reuse count, consumer algebra, and every externally visible shape or value.
2. Estimate preparation and padded-work cost against repeated boundary cost:

   ```text
   net_candidate_cost = preparation + padded_storage_traffic + inactive_compute
                        - repeated_boundary_work_removed
   ```

3. Define the neutral value per consumer. Zero is neutral for dot and sum; max needs its lower identity, min its upper identity, and normalization requires padded positions to be excluded from semantic statistics.
4. Prefer direct producer writes into the padded layout. If a standalone pad is unavoidable, benchmark it as part of the public call.
5. Pass logical extents separately and retain semantic masks. Physical exactness proves address safety only; it does not prove padded positions are valid data.
6. Compare padded, effective-extent, and masked-tail candidates with identical useful work, precision, and output semantics.
7. Gate the padded representation by shape when its benefit is not stable, and keep the generic fallback.

## Semantic Examples

- A zero-padded GEMM K lane contributes zero to the contraction.
- A zero-padded key row in attention has score zero and would contribute `exp(0)`; the key-validity mask must still exclude it from maximum and denominator state.
- A max reduction needs a lower identity rather than zero when valid values may be negative.
- A padded grouped operation must retain per-group logical lengths so one group's padding cannot leak into another group.

## Variant: Zero-Pad A Contraction Dimension To Unmask Hot-Loop Loads

When IR shows that the active compiler lowers a masked `tl.load` to a conditional fill-plus-copy path and that path is costly, zero-pad the contraction or reduction dimension to a multiple instead of carrying a tail mask on every iteration: pad the activation buffer with zeros and pad the weight matrix with zero columns. Padded lanes then contribute exact zeros, every hot-path load becomes unmasked, and only the store keeps an output-bound mask (plus an optional channel-tail mask for the output rows). This works for non-idempotent reductions and contractions where the overlap-load trick (`overlap-tail-load-mask-free`) does not apply.

Rules:

1. Choose the pad multiple and the block width **together**: pad the extent to the **smallest** multiple that keeps waste small, and set the block width to the **largest** block that divides the padded extent. Do not enlarge the pad just because a larger block would divide it: a pad that adds tens of percent of fake reduction work can lose more than the deeper iteration count saves.
2. Pad the weights once at build/cache time (zero columns beyond the real extent) and cache per shape/dtype. Pad the activation with zeros; if the buffer is reused across calls, only the borders/pad lanes need zeroing once, since the interior is fully overwritten each call.
3. Keep exactly one store-side mask for the real output extent; add a channel/row mask only when output rows are not block-divisible.
4. Split addressing origins carefully: the padded buffer's strides use the **padded** dim, while the output/store strides must keep the **real** dim. Getting this wrong corrupts only batched cases; batch-1 tests hide it.
5. Set dispatch gates at **measured break-even**, not round-number heuristics: probe the padded vs masked variant in isolation across the shape family first, then encode the measured crossover. Dispatch-only changes are the cheapest validation unit and can be probed independently of kernel-body edits.

Avoid this variant when padding bytes dominate (the extent is far below the tile multiple and the pad cannot be amortized), when the op is nonlinear across the padded lane in a way zeros do not neutralize (e.g. softmax denominators over padded lanes, or reductions that must know the true extent), or when the store cannot be masked (pure in-place, aliasing, or externally visible padded extents).

Verify differential correctness on non-divisible and batched shapes (a wrong origin split fails only higher batches), confirm the hot-path loads lose the fill-plus-copy form in IR while the store still masks the real extent, compare pad-multiple/block combinations per shape family, and confirm the padded weights and buffers are cached rather than rebuilt per call.

## Generalization

Candidate families include irregular Linear/GEMM panels reused across output tiles, grouped or batched contractions, MoE expert batches with internal token capacities, convolution or patchification panels reused by matrix work, and head-, group-, or channel-blocked intermediates. Attention head padding is one instance of the storage decision, not the definition of the pattern.

## Pattern Ownership

- This card owns the decision to introduce and cost an internal neutral-padded physical representation.
- `exact-tile-no-boundary-fast-path` owns deleting boundary-only predicates after the padded physical extents make exact coverage provable.
- `intermediate-layout-copy-deletion` owns avoiding a separate layout bridge by changing producer stores or consumer indexing.
- `pad-copy-row-col-tiling` owns efficient implementation of an unavoidable standalone constant-pad copy.
- `implicit-transpose-elimination` owns physical dot-operand orientation and cached prearrangement of invariant operands.
- `live-length-tiling` owns the competing strategy of shrinking work to the live extent.
- `kernel-fusion-and-value-placement` owns launch grouping; a shared padded boundary does not imply fusion.

## What To Verify After Applying

- Full correctness across zero, exact, one-past-boundary, and large-tail extents for every supported dtype and semantic mode.
- Every padded lane is initialized with the required neutral value and cannot affect valid outputs, NaN/Inf behavior, normalization state, or group boundaries.
- Logical extents remain authoritative for public shapes, semantic masks, and stores.
- Preparation, allocation, padded bytes, inactive compute, cache misses, and recovery copies are included in total-operation latency.
- Profile and IR confirm repeated boundary work disappeared and was not replaced by a worse transfer, layout, or resource path.
- Padded, effective-extent, and masked fallbacks are compared across representative shapes; shape dispatch covers regimes where padding regresses.

## Related Patterns

- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md)
- [intermediate-layout-copy-deletion](./intermediate_layout_copy_deletion.md)
- [pad-copy-row-col-tiling](./pad_copy_row_col_tiling.md)
- [implicit-transpose-elimination](./implicit_transpose_elimination.md)
- [live-length-tiling](./live_length_tiling.md)
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md)
- [现有知识：care_padding：padding 填充行为与并行度影响](../techniques/care_padding.md)
