---
type: Optimization
title: Reduction Axis Split And Combine
description: 当非归约维 grid 无法填满核数时，把归约轴拆分到多个 program，各自产出部分归约状态再由轻量 combine 合并。
tags: [task.optimization, topic.compute.reduction, topic.parallelism]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/reduction-axis-split-combine.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Reduction Axis Split And Combine

## Summary

When a reduction kernel's parallelism is capped by its non-reduction grid (the launch cannot fill the cores), split the REDUCTION axis across programs. Each program emits a partial reduction state (accumulator plus auxiliary state such as max/denominator/count), and a light combine kernel merges partial states according to the reduction algebra.

## Use When

A reduction kernel (sum, softmax, top-K, dot over K) sizes its grid from the
non-reduction dimensions only and cannot fill the device even after tile
resizing: for example a per-row reduction over `[4, 1M]` launches 4 programs
on a 32-core device, each looping over the long reduction axis while the
other 28 cores idle.

Two preconditions: the reduction admits cheap associative partial states — an
fp32 partial sum, online-softmax state (accumulator, running max, running
sum), or counts — that a light combine pass can merge, and each program after
the split still has enough work that the partial-state write and combine cost
pays off.

## Avoid When

- The unsplit grid already fills the cores.
- Splitting drops per-program work below the work floor.
- The reduction has no cheap closed-form combine (e.g. order-sensitive recurrence without a compensating state).
- The active contract pins per-slice quantization: splitting changes the quantization points and the merge is only associative, not bit-identical. Land the compensated precision layer first (`hilo-split-matmul`).

## Signals

### Profile

- Core occupancy under one program batch while the kernel is latency-bound; combine-eligible state is small relative to the output.

### Code

- A single loop over the reduction axis inside a program whose grid has no reduction-axis factor.
- Grid = f(non-reduction dims) such as `S_q * ceil(N_q / BLOCK_H)`: the small-`S_q` regime leaves a program count far below the physical core count while the reduction loop still runs many iterations, and the large-`S_q` regime fills the device.

## Rewrite Goal

```python
# pass 1: grid = (..., num_splits)
partial_acc[pid, split] = reduce_over_slice(...)   # fp32
partial_aux[pid, split] = (running_max, running_sum, ...)
# pass 2: grid = (...,)
final = combine(partial_state[:, 0], partial_state[:, 1], ...)  # same algebra, applied pairwise
```

## What To Verify After Applying

- Partial states are associative-mergeable and stored in fp32; combine order matches the reduction algebra.
- Split depth respects the work floor and the concurrency cap.
- Re-derive the split depth after any change to the consumer grid or operand
  precision: head-side batching (`gqa-kv-shared-row-batching`) halves the base
  program count, so a split tuned before batching may stop firing or start a
  second program batch.
- Numerics within tolerance of the unsplit form (online-softmax state merges are associative but not bit-identical). If the result fails, first identify whether the change came from reduction reassociation, state merging, or dot operand precision. Use `hilo-split-matmul` only when the evidence isolates dot precision as the cause; otherwise keep the unsplit fallback.
- Partial state is extra live UB, so size the split jointly with the tile per `tile-footprint-fitting`.

## Related Patterns

- [dot-matmul-rewrite](./dot_matmul_rewrite.md): the unsplit reduction structure this pattern parallelizes.
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md): split depth is a shape-regime parameter.
- [autotune](../operator_optimization/autotune.md): split factor is a tunable with the work floor as a bound.
- [现有知识：分核优化](../operator_optimization/vector_core_partition.md)
