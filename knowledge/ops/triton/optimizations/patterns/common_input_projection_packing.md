---
type: Optimization
title: Combine Linear Projections That Read the Same Input
description: 把消费同一输入的兄弟仿射投影合并为一次更宽的收缩或共调度收缩，复用彼此的输入读取。
tags: [task.optimization, topic.compute.composite, topic.data_movement.data_copy]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/common-input-projection-packing.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Combine Linear Projections That Read the Same Input

## Summary

Group compatible sibling affine projections that consume the same input as either one wider contraction or co-scheduled contractions that reuse each loaded input tile. Both forms share input traversal and launch setup while preserving independent parameter values, output semantics, and downstream ownership.

## Use When

Several linear projections consume the same input and reduce over the same
dimension (K), differing mainly in their output channels — a generic shape,
with Q/K/V-style siblings as the canonical instance:

```python
Q = x @ W_q        # separate kernels, each re-reading the same x
K = x @ W_k
V = x @ W_v
```

The same shape appears wherever sibling projections share one input — gated
FFN gate/up pairs, Mamba `in_proj` branches, multi-head prediction heads —
not only in attention. Profiling shows the sibling kernels repeating the same
input loads, contraction-loop setup, and launch overhead. The parameters are
immutable or cacheable long enough that packing them (transposition,
concatenation) can be amortized outside the measured hot path, the outputs
can stay disjoint (stride-aware views of one packed result or separate stores
without cross-program communication), and the combined width still admits a
legal, efficient tile/grid plan on the target.

## Avoid When

- Siblings require different reduction extents, input rows, quantization scales, bias/activation semantics, rounding points, accumulator types, or mutation/alias behavior that one contraction cannot preserve.
- A wider output axis or multiple live sibling accumulators create material tail padding, poor program-batch fill, excessive accumulator/UB pressure, or a slower store lowering that outweighs the shared input work.
- Preparing or packing parameters, or restoring layouts, occurs on every measured call and is not repaid by the saved launches and input traversal.
- Downstream consumers need incompatible schedules and a consumer-native multi-destination epilogue lowers worse than a regular packed store plus views or a retained split.
- A split projection is required for independent synchronization, external visibility, parameter updates, or a specialized backend/library path.

## Signals

### Code

- Several `linear`, GEMM, or `tl.dot` launches read the same `[rows, reduction]` input and use separate `[reduction, output_i]` weights.
- Projection results are immediately sliced, reshaped, transposed, or forwarded to different consumers.
- A wrapper constructs one wider random layer instead of preserving the original sibling parameters, silently changing the numerical reference.

### Profile

- Sibling projection kernels repeat the same input DMA and K-loop handshakes.
- Projection launches are individually narrow or launch-bound, while their combined output width would fill tiles or program batches better.
- A packed or co-scheduled contraction wins, but its multi-destination epilogue is disproportionately expensive relative to an ordinary single-destination projection.

### IR

- A packed dot or co-scheduled sibling dots remain regular, but segmented masked, indirect, or strided stores prevent a direct Fixpipe/store path available to ordinary outputs.
- Grouping changes accumulator footprint, buffering, or store tiling enough to require a different legal tile from the separate projections.

## Method

Confirm the fit first: inventory the sibling projections' input rows,
reduction dimension, dtypes, bias/rounding semantics, and output
destinations; profiling should show the siblings repeating the same input
loads and launch overhead.

The optimization core is to choose a contraction form (the ladder below) and
an output placement (the second ladder) independently, always measured
against a strong separate-projection baseline with the same physical weight
orientation and legal tiles. Keep input, math, parameter values, per-output
accumulation order, and public output semantics fixed while comparing forms.

- Benchmark regular packed or separate contiguous outputs before
  consumer-native epilogues, to isolate input/launch reuse from epilogue
  lowering.
- Recompute padding lanes, program count, program batches, and accumulator/UB footprint
  for the selected form — co-scheduling multiplies the live accumulators.
- Validate total-operation latency across row-count and output-width regimes;
  shape-gate only on causal properties such as padding ratio, legal tile, or
  program count.

## Semantic Construction Contract

Packing is a schedule and storage transformation, not a parameter redefinition. Preserve the original parameter values and their externally observable construction order first, then form the packed cached representation:

```python
# Preserve the original modules/parameters and their initialization order.
w0 = first_weight.detach().transpose(0, 1).contiguous()
w1 = second_weight.detach().transpose(0, 1).contiguous()
w2 = third_weight.detach().transpose(0, 1).contiguous()

# Pack only the physical contraction representation.
w_packed = torch.cat((w0, w1, w2), dim=1)
```

Do not replace independently initialized parameters with one newly initialized wider parameter merely because the shapes concatenate. A co-scheduled form may keep the original physical weights separate; a packed form may build a concatenated cached representation. For cached prepared weights, the cache key and invalidation rule must cover device, dtype, logical dimensions, physical layout, transform form, and the parameter identity/version required by the mutation contract.

## Contraction Form Ladder

Evaluate how the common input is shared separately from output placement:

1. **One packed contraction.** Concatenate compatible physical weights along the output axis and compute one regular wider result. This is usually the simplest form when the combined width has a strong tile and one contiguous output is acceptable.
2. **Co-scheduled sibling contractions.** One program loads an input tile once, walks one shared reduction loop, and updates independent accumulators with each sibling's weight tile. This can preserve natural per-output tiles and destinations when one concatenated width lowers poorly, but all sibling accumulators remain live together.
3. **Partially grouped contractions.** Pack or co-schedule only a compatible subset when one sibling's width, precision, layout, or resource footprint blocks the group.
4. **Original separate projections.** Retain as the semantic and performance fallback.

Treat co-scheduling as computational reuse, not mere launch coalescing: verify in source and IR that the input tile and reduction traversal are actually shared. Choose accumulator tiles jointly; a tile that is legal for one projection can exceed UB/register capacity after multiplying the live accumulator count.

### Co-scheduled pairing with unequal block counts

When co-scheduled siblings have different output block counts, pair their blocks on the **same grid axis**: program `i` computes one block of sibling A and one block of sibling B; the majority side covers the axis and a **scalar condition** masks the minority side's accumulator, loads, and store so its absent blocks are never written. Load the shared input tile once per iteration and feed both siblings' dots from it.

- Keep each output's per-element accumulation order (the same reduction chunking as the separate kernels). If the fused form re-chunks the reduction axis, expect a small rounding-order difference and validate it through the differential contract.
- The fused form carries both accumulators plus both siblings' weight tiles; a wider dtype whose tile bytes double can overflow UB. Gate the co-scheduled form on dtype and keep the separate kernels as the fallback.
- Verify the minority-side tail: masked-out blocks must not be stored. Compare fused vs separate on the combined kernel time, then through the canonical end-to-end comparison.

## Output-Placement Ladder

Evaluate output placement separately from the common-input contraction:

1. **Regular packed output plus views.** Store one contiguous `[rows, sum(output_i)]` result and expose disjoint stride-aware slices. This is the cleanest control for the contraction/launch benefit.
2. **Consumer-native segmented epilogue.** Route each packed interval or sibling accumulator to its required physical destination, including a transposed or otherwise affine segment when legal. This can delete downstream layout materialization.
3. **Partially grouped outputs.** Keep compatible siblings together and split only the output whose layout, precision, or epilogue blocks the fast path.
4. **Original separate projections.** Retain as the semantic and performance fallback.

For segmented stores, write down every output interval and destination mapping. A tile that crosses an interval boundary may need several mutually exclusive masks. Padding each interval to a tile boundary can simplify stores but adds contraction lanes; compare that cost with one concatenated width and with the regular packed-output control.

## Generalization Beyond Attention

The same structure appears in gated feed-forward blocks, recurrent/state-space gate matrices, multi-head prediction branches, and other sibling affine maps that share one activation matrix. The transferable mechanism is common-input contraction grouping; the number and names of output partitions are operator-specific evidence, not part of the rule.

## Pattern Ownership

- `kernel-fusion-and-value-placement` owns the decision to group sibling nodes and the general legality/profitability gate.
- This card owns the common-input affine implementation after sibling grouping is selected: packed versus co-scheduled contraction form, parameter packing, output-axis partitioning, and the regular-versus-segmented epilogue ladder.
- `host-launch-coalescing` owns repeated submission of unchanged logical kernels; it does not share one contraction's input traversal.
- `intermediate-layout-copy-deletion` owns deletion of affine layout bridges at the selected output boundary.

## Related Patterns

- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md)
- [intermediate-layout-copy-deletion](./intermediate_layout_copy_deletion.md)
- [implicit-transpose-elimination](./implicit_transpose_elimination.md)
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md)
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md)
- [dot-matmul-rewrite](./dot_matmul_rewrite.md)

## What To Verify After Applying

- Parameter values, initialization order, bias/quantization semantics, rounding points, mutation behavior, and every externally visible output match the parent.
- All output partitions have disjoint, complete ownership; boundary tiles, odd partition counts, and padded channels neither overlap nor escape their logical intervals.
- Parameter packing or other preparation is amortized or included in the measured metric, and cache invalidation is correct.
- Compare separate projections, a regular packed contraction, co-scheduled sibling contractions, consumer-native output placement, and any partial grouping at matched contraction precision and tile intent.
- Inspect main-dot legality, accumulator/UB footprint, program batches, padding work, store op class, and direct Fixpipe/store eligibility.
- Report component and total-operation latency across representative row and output-width regimes; keep the separate implementation as fallback outside validated regimes.
