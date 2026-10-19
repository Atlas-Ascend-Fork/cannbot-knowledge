---
type: Optimization
title: Compute Shared Values Once and Store Them in GM
description: 在受支持的 kernel 边界把昂贵共享值计算一次写入 GM，消费者按需读取，替代各 program 重复计算。
tags: [task.optimization, topic.memory, topic.data_movement.data_copy]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/compute-once-share-via-gm.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Compute Shared Values Once and Store Them in GM

## Summary

Compute an expensive value once at a supported kernel boundary, write it to GM, and let consumer programs load it instead of recomputing it. This trades an extra GM write/read, allocation, and synchronization for deleted computation.

## Use When

Several consumer programs (or launches) each recompute the same expensive
value because it does not depend on the axis that distinguishes them — for
example every program in a grid recomputes an input-wide statistics table
that is identical for all of them — and profiling confirms the repeated
computation is material, not just visible in source.

The trade pays off only when reuse is high and the shared value is small: one
GM write plus the consumer reads must cost less than the repeated production.
A safe handoff for the shared value must exist — typically a separate kernel
launch or an existing output slot. The baseline must be compute-bound, with
enough MTE/GM headroom to absorb the added write/read traffic. Rule out
cheaper alternatives first — deleting the duplicate work, LICM, algebraic
simplification, or on-chip sharing through changed ownership (see the
adoption order below).

## Avoid When

- The design requires arbitrary unsynchronized cross-program GM communication within one Triton launch; a store by one program does not make a legal, synchronized producer-consumer boundary for other programs.
- On-chip sharing, loop-invariant hoisting, algebraic simplification, changed ownership or tiling, or direct forwarding can remove the duplicate work without a GM round trip.
- The producer is cheap, reuse is low, the published value is large, or the workload is already MTE/GM-bound.
- The candidate would publish a full attention score or probability tensor with quadratic `O(N^2)` storage and traffic merely to avoid recomputation.
- Observable dtype or rounding semantics, allocation cost, synchronization requirements, ownership, layout, or execution-engine placement make the comparison illegal or unprofitable.

## Establish The Reuse Proof

Name the producer's logical index domain and the consumer program domain. Identify the consumer-only axis absent from the producer indices, then count how many consumer programs reproduce each producer value after masks and boundary tiles are considered. Confirm that the values are identical under required dtype, rounding, masking, and random-state semantics; matching source expressions or tensor shapes alone is not proof.

Locate the actual publication boundary. Separate Triton launches provide ordered visibility through the surrounding runtime, and an existing output or byproduct may already provide legal storage. Within one launch, arbitrary programs cannot communicate through GM without an explicit synchronization mechanism supported by the target; do not infer a barrier from program order or grid geometry.

## Adoption Order

Prefer the first legal, profitable option in this order:

1. Delete unnecessary producer or consumer work.
2. Reuse within the same program or apply LICM so the value remains in registers or UB.
3. Simplify the mathematics or replace the producer with a cheaper equivalent.
4. Change ownership, tiling, fusion placement, or forwarding so consumers share or directly receive the value on chip.
5. Only then publish the value through GM at a legal boundary to eliminate cross-program recomputation.

The pattern is classified as **structural** because it changes kernel boundaries, ownership, and dataflow. Its implementation is nevertheless late and evidence-gated: apply it only after cheaper structural and kernel-local alternatives have failed and a matched cost comparison supports publication.

## Cost Model And Matched Comparison

Use measured target costs where possible and include execution multiplicity:

```text
recompute_cost =
    producer_cost_per_value_or_tile
    × consumer_programs_recomputing_it
    × produced_value_or_tile_count

publication_cost =
    producer_cost_once
    + gm_write_cost
    + (gm_read_cost_per_consumer × consumer_count)
    + allocation_cost
    + launch_or_synchronization_cost
```

Publication is plausible only when `publication_cost < recompute_cost` after accounting for changed tiles, occupancy, engine placement, and total-operation latency. Compare variants with identical producer math, consumer schedule, output semantics, and representative shapes where possible: first measure recomputation at the same legal boundary, then change only publication/loading. If the boundary forces another schedule or engine, report that confounder rather than attributing the whole difference to deleted recomputation.

## Signals

### Code

- A producer expression or reduction sits inside code indexed by a consumer-only program axis that does not affect the producer's inputs.
- Multiple launches or consumer families reconstruct the same compact value from the same source data.
- An existing output, side output, or workspace can legally carry the reusable value without exposing a new quadratic intermediate.

### Profile

- Producer instructions or engine time scale with consumer-program count although the producer's logical domain does not.
- Compute engines dominate while GM bandwidth and MTE utilization retain headroom.
- A matched variant shows that deleting repeated producer work outweighs the added write, reads, allocation, and boundary overhead.

## Related Patterns

- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): choose grouping, ownership, and selected-value placement before accepting a GM boundary.
- [algebraic-optimization](./algebraic_optimization.md): simplify or factor the producer before deciding that its result should be stored.
- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md): keep invariants within one program when registers or UB can span their uses.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): change program ownership to create on-chip reuse before publishing through GM.
- [attention-online-softmax-fusion](./attention_online_softmax_fusion.md): attention can expose large repeated producers, but full score/probability publication is a high-risk quadratic example rather than the scope of this generic pattern.
## What To Verify After Applying

- Reference outputs, including dtype, rounding points, masks, NaN/Inf behavior, random-state behavior, layouts, and every externally visible output or byproduct.
- Actual producer execution count and consumer reuse count, rather than inferred graph-level fan-out.
- GM bytes, MTE utilization, allocation/workspace size, launch and synchronization overhead, and absence of unsynchronized intra-launch communication.
- UB/register pressure, spills, occupancy, legal tile choices, and execution-engine placement in compiler output and profiling.
- Component and end-to-end latency across representative and boundary shapes, using a matched baseline that isolates deleted recomputation from unrelated schedule changes.
