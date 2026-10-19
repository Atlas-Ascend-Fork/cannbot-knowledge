---
type: Optimization
title: GQA/MQA KV-Shared Row Batching
description: 把共享同一 KV head 的独立 query 行批入同一 program，使只读 K/V tile 每份只加载一次。
tags: [task.optimization, topic.attention, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/gqa-kv-shared-row-batching.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# GQA/MQA KV-Shared Row Batching

## Summary

Batch independent query-row computations that share one KV head into the same program, so each read-only K or V tile is loaded once while every row keeps its own scores, normalization state, accumulator, and output. In attention this can be decode row folding inside one online-softmax kernel, or a small query-head group inside separate QK and PV stages whose intermediates are written to memory.

## Use When

Your operator is GQA/MQA attention: `N_q` query heads share `N_kv` KV heads
with group size `G = N_q / N_kv > 1` (Q is `[B, S, N_q, D]`, K/V are
`[B, S_kv, N_kv, D]`), and the kernel runs one program per query head (or per
query position and query head). The `G` sibling programs in a KV-head group
iterate the same `S_kv` range over the same K/V offsets, so each shared K/V
tile is loaded `G` times. A typical shape:

```python
head_kv = (pid % N_q) // G    # G sibling programs share this KV head
k = tl.load(K + head_kv * skh + kv_offs[:, None] * sks + d_offs[None, :])
```

Profile shows the re-reads are material: decode cases are HBM/L2-bound on
K/V with traffic near `G` times the logical cache size, or a Vector-dominated
profile shows `G` redundant consumer programs.

Two forms apply, depending on the kernel's current structure:

- **Decode fold**: decode or other small-`S` shapes, where query positions and
  the head group are small enough to fold into one online-softmax row tile
  that still fits.
- **Separate-stage grouping**: QK, normalization, and PV are already separate
  stages, so a bounded head group can share a K or V tile inside the
  contraction stages without duplicating normalization state.

Applying this pattern cuts shared K/V loads from `G` per KV head to one, at
the cost of extra live accumulators and masks.

## Avoid When

- Prefill or large `S` in one online-softmax kernel: at a fixed row budget, folding may not reduce K/V reads, and multiple live max/sum/accumulator states can force a narrower key tile and more serialized recurrence iterations. Prefer the ordinary per-query-head kernel or the separate-stage variant below.
- `G == 1` (MHA) with `S * GT < 16`: padded rows waste most of the dot.
- `S_kv` iteration count is 1 on this compiler: 3D-load + reshape kernels hit a UB planner bug at single-iteration KV loops; keep `S_kv / BLOCK_KV >= 2` or use the 2D kernel.
- The shared operand is small or cache-resident enough that grouping adds accumulators, masks, and control without reducing transfer time.

## Signals

### Code

- Decode kernel loops `for s in range(S)` inside each program and re-reads every K/V tile per `(s, head)`.
- The grid contains `G` programs per KV head doing identical K/V DMA.
- Separate QK or PV kernels use one query head per program even though adjacent heads address the same K or V base tile.

### Profile

- Decode cases are HBM/L2-traffic-bound on K/V; total K/V traffic is `G` times the logical cache size.
- Grouping an online path reduces loads but regresses after its key tile narrows or its recurrence iteration count grows.
- A Vector-dominated (not traffic-bound) profile with `G` redundant consumer programs is still a valid trigger: the cost being removed is the duplicated per-program staging work, not HBM bytes. Do not require an HBM/L2-traffic-bound profile before grouping.

## Method

Confirm the fit first: profile or IR shows each K/V tile loaded once per query-head sibling, and the reloads or duplicated staging are a material cost. Record the baseline: per-program tile sizes, recurrence iterations, transferred bytes, and the operand-precision path that will actually run.

The optimization core is to give the rows that share one KV head to a single program (or to shared contraction stages), so that program loads each K/V tile once while every row keeps independent state.

### Rule: Fold decode rows and the head group into one tile

Grid: `(B * N_kv,)`. Program decodes `batch = pid // N_kv`, `head_kv = pid % N_kv`, `G = N_q // N_kv`. Build the `[S, GT, D]` query tile with one 3D load using a clamped head index, then `tl.reshape` to `[S * GT, D]`:

```python
s_idx = tl.arange(0, S)
g_idx = tl.arange(0, GT)
g_c = tl.minimum(g_idx, G - 1)          # clamped, plain arange only
q3 = tl.load(Q + b * sqb + s_idx[:, None, None] * sqs
             + (head_kv * G + g_c)[None, :, None] * sqh + d_offs[None, None, :])
q = tl.reshape(q3, (S * GT, D))
# per-row query position for the causal mask, also without // or %:
s_row = tl.reshape(tl.broadcast_to(s_idx[:, None], (S, GT)), (S * GT,))
```

Run the ordinary online-softmax KV loop once per program on the folded tile. The displayed causal mask assumes a right-aligned KV/query position convention: `kv_offs[None, :] <= s_row[:, None] + (S_kv - S)`. Derive the mask from the operator's actual position mapping when its convention differs. Store with `tl.reshape(acc, (S, GT, D))` and mask `g_idx < G`. K/V tile reads drop from `G` per KV head to 1, and the dot M-dim grows from `GT` to `S * GT`.

### Rule: Size the fold to the head group, not to `G * S`

`GT = next_pow2(max(16, G))` — cover the `G` distinct heads, no more. Rows beyond `G` are clamped duplicates and waste dot compute ~`S`x for `G > 16`. When the head count is below the group width, the extra rows are masked lanes that waste dot lanes, so dispatch a narrower row tile for that regime.

### Rule: Build folded indices with broadcast_to + reshape

Build row indices and causal positions with `broadcast_to` + `reshape` of a plain (clamped) arange for the affected compiler path. Record the target/compiler version and verify whether `//` and `%` on index vectors feeding `tl.dot` compile before relying on this restriction.

### Rule: Keep the fold inside the row and tile budget

`BLOCK_KV = 256` wins for small `S` but can fail to compile as `S * GT` grows; gate per `(S, D)`. Rows beyond the fold budget hit a UB planner overflow in 3D-load + reshape kernels, so keep the fold inside the budget.

### Rule: Group query heads inside separate stages when the fused fold does not fit

Retain the stage boundaries and group a small number of query heads only inside the contraction stages:

- **QK stage:** load one shared K tile, load one Q tile per grouped query head, and emit independent score tiles.
- **PV stage:** load one shared V tile, load one normalized-weight tile per grouped query head, and maintain one output accumulator per head.
- **Normalization stage:** keep rows independent; do not share max/sum state merely because the KV operand is shared.

Start with the smallest useful group, often two adjacent query heads, and mask the last group when `N_q` is not divisible by the group width. Recompute the live accumulator footprint and tile fit separately for QK and PV. A group size that helps a separate Cube stage can strongly regress a fused online path if it forces a smaller key tile or doubles the serialized Vector recurrence. This variant generalizes to sibling contractions with a shared read-only operand and disjoint outputs: batch only the consumer axis that creates real operand reuse, and keep per-consumer reduction or normalization state independent.

Discipline: re-derive the folded or grouped configuration's fit with the operand precision that will actually run. A group width that overflows UB at fp32 operand precision can fit once matched lower-precision operands plus `hilo-split-matmul` shrink the footprint; re-run `large-tile-fit-enabling` instead of inheriting the earlier overflow verdict. Validate QK, normalization, and PV separately, and confirm the win by measurement on the operator's own shapes — the separate-stage variant and the fused online path respond differently to the same group width.

## Related Patterns

- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): generic adjacent-row ownership and per-program reuse.
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): decide whether online fusion or retained separate stages provide the better schedule that fits.
- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): account for the serialized normalization state that can make online head grouping regress.
- [engine-aware-grid-scheduling](./engine_aware_grid_scheduling.md): map the grouped logical work after the ownership change is fixed.
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md): retain grouping only for validated query-depth, head-group, and tile-fit regimes.
- [现有知识：Attention 优化经验聚合](../experiences/attention_experiences.md)

## What To Verify After Applying

- Every query position and query head is covered exactly once, including odd final head groups and causal row positions.
- Shared K/V loads decrease in the emitted IR or profile rather than only in source notation.
- Each row keeps independent score, max, sum, accumulator, and output semantics.
- Group width, key tile, recurrence iterations, UB/accumulator footprint, program count, and total latency are reported for decode-folded, separate-stage, and rejected online-grouping candidates separately.
- Generic per-head fallbacks cover large query depth, `G == 1`, live sets that do not fit, and regimes without reuse benefit.
