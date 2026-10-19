---
type: Optimization
title: Attention Intermediate Vector Work Reduction
description: 缩短混合 attention kernel 中 Cube 生产者到 Vector 变换再到 Cube 消费者的串行路径，删除、共享或重塑中间 Vector 工作。
tags: [task.optimization, topic.attention, topic.implementation.pipeline]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/attention-intermediate-vector-work-reduction.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Attention Intermediate Vector Work Reduction

## Summary

Shorten the serialized Cube producer -> Vector transformation -> Cube consumer path in a mixed attention kernel by removing, sharing, or reshaping intermediate Vector work between the two Cube operations. Treat every rewrite as a measured candidate because fewer source operations do not guarantee a shorter lowered path.

## Use When

In a mixed attention kernel, a first Cube operation such as QK produces a tile
that Vector scale, mask, normalization, or recurrence work must transform
before a second Cube operation such as PV can start, and profiling shows the
downstream Cube operation actually waiting on this intervening Vector phase —
for example Vector-dominated engine ratios with an idle Cube — rather than
the Vector work being hidden by overlap or dwarfed by transfer time. Code or
IR shows duplicated or unnecessarily sequential Vector expressions whose
result directly gates the downstream Cube consumer.

## Avoid When

- The candidate removes fully invisible attention tiles or peels fully valid tiles; use `attention-visibility-mask-specialization`.
- The rewrite is an ordinary algebraic identity without a measured Cube -> Vector -> Cube serial-path issue; use `algebraic-optimization`.
- The decision is whether a producer should be fused, recomputed, stored, or moved across a kernel boundary; use `kernel-fusion-and-value-placement`.
- The decision changes the complete `exp`/`log` versus `exp2`/`log2` convention; use `normalization-base-convention-ablation`.
- The candidate only flips the Cube-produced intermediate from `[N, M]` to `[M, N]` so Vector sees a different L0C-to-GM orientation; use `cv-intermediate-tile-orientation`.
- The kernel is pure Vector, the second Cube consumer is independent of the targeted Vector result, or memory transfer dominates the measured path.

## Signals

### Code

- A `tl.dot` score tile is followed by several elementwise temporaries before that transformed tile feeds another `tl.dot`.
- The same tile-shaped expression, such as `scores * sig`, is computed in both normalization statistics and the normalized score update.
- Vector intermediates remain live across the transition into the consumer dot.

### Profile

- Cube work appears on both sides of a substantial Vector interval and the downstream Cube phase waits for that interval.
- Reducing only the intervening Vector expression count changes kernel latency or the Cube/Vector timeline without changing recurrence trips or transferred bytes.
- Vector instruction, special-function, or synchronization cost grows with the score-tile shape on the serialized path.
- Vector-dominant engine balance with an idle Cube and light transfer: e.g. `aiv_vec_ratio` ~0.89-0.97 together with `aic_mac_ratio` ~0.03-0.06 and `aic_mte2_ratio` <0.05, while achieved throughput sits far below the bandwidth floor. This localises the cost to a serialized Vector/staging path, but it does NOT say which Vector work is removable — validate with a complete-form candidate before attributing (see `gather-then-dense-compute`'s Pairing And Refutation Protocol).

### IR

- The lowered graph contains duplicate multiply/add/select chains between two dot-like operations.
- A shared source expression is rematerialized instead of reused, or a temporary extends the live range into the consumer dot.
- Waits or scheduling barriers preserve a producer-to-Vector-to-consumer dependency that source-level overlap cannot hide.

## Method

Confirm the fit first: profiling and IR must show the Vector interval between
the two Cube operations serialized and material — the downstream Cube waits
on it — with recurrence trips, transferred bytes, tile sizes, and math
convention recorded as the fixed control baseline.

The optimization core is to shorten that serialized Vector interval by
removing, sharing, or reshaping the Vector expressions whose result gates the
consumer dot. Build one candidate at a time from the levers below; do not
combine it with work deletion, tile changes, boundary movement, or
exponential-base changes. Keep the rewrite only if IR shows the targeted
Vector chain actually shorter and total latency improves without harmful UB
growth or a worse Cube schedule; if IR is unchanged or latency does not
improve, pivot to the routed pattern matching the evidence instead of adding
unrelated tuning knobs.

Levers, from most to least common:

### Lever: Share a repeated tile-shaped subexpression

An online normalization step may independently form `scores * sig` for the
row maximum and again for the normalized weights consumed by PV; compute it
once:

```diff
- row_max = tl.maximum(row_max, tl.max(scores * sig, axis=1))
- normalized = scores * sig - row_max[:, None]
- probs = tl.exp(normalized)
- acc = tl.dot(probs.to(value_dtype), values, acc)
+scaled_scores = scores * sig
+row_max = tl.maximum(row_max, tl.max(scaled_scores, axis=1))
+normalized = scaled_scores - row_max[:, None]
+probs = tl.exp(normalized)
+acc = tl.dot(probs.to(value_dtype), values, acc)
```

This candidate removes one score-tile Vector multiply from the dependency
chain when the compiler otherwise emits it twice. Inspect IR because the
compiler may already perform common-subexpression elimination, while explicit
sharing may instead lengthen a live range.

### Lever: Replace special-case recovery selects with a sentinel value

A common online-softmax body masks scores with `-inf` and then spends several
tile-shaped selects recovering from the `-inf` special cases:

```diff
- score = tl.where(valid, score, float("-inf"))
- m_new = tl.maximum(m_i, tl.max(score, axis=1))
- m_safe = tl.where(m_new == float("-inf"), 0.0, m_new)
- alpha = tl.exp2(m_i - m_safe)
- alpha = tl.where(m_i == float("-inf"), 0.0, alpha)
- p = tl.exp2(score - m_safe[:, None])
- p = tl.where(valid, p, 0.0)
+ score = tl.where(valid, score, -65504.0)   # fp16 min: p underflows to 0
+ m_new = tl.maximum(m_i, tl.max(score, axis=1))
+ row_has_valid = tl.max(valid.to(tl.int32), axis=1)
+ m_safe = tl.where(row_has_valid, m_new, 0.0)   # all-masked row: p underflows, l_i stays 0
+ p = tl.exp2(score - m_safe[:, None])
+ alpha = tl.where(l_i > 0.0, tl.exp2(m_i - m_safe), 0.0)
```

The `-65504` sentinel can replace the validity select only when every valid row maximum is bounded so that invalid sentinel values underflow in `exp2(score - m_safe)`. For an all-masked row, use `m_safe = 0` and keep `l_i == 0`; for an unbounded or very negative valid score range, retain the original `-inf` path. Verify the sentinel range, finite outputs, and all-masked rows before keeping this rewrite.

### Lever: Fold a scalar into an already-required expression

Merge a standalone tile-shaped scale into an expression the chain already
computes, so no extra tile pass exists at all.

### Lever: Shorten a temporary's live range

Re-derive a small value near its consumer instead of keeping a full tile
temporary live across the Cube/Vector transition.

### Lever: PV operand precision

Route to `dot-operand-precision-ablation` first for the equal-work dtype
control, then apply the attention-specific probability and recurrence checks
below.

## Attention-Specific PV Precision Boundary

Use `dot-operand-precision-ablation` for the generic matched-operand experiment, accumulator separation, bidirectional controls, and fallback rules. In online attention, additionally freeze max, denominator, recurrence scaling, exponential convention, mask paths, and output placement.

Probability cast location is part of the attention semantics. Casting the normalized exponent input before `tl.exp`, casting probabilities after `tl.exp`, and using rounded versus unrounded probabilities for the denominator are not equivalent. Isolate each form and validate sharp score distributions, tiny nonzero probabilities, long sequences, and scale extremes. FP32 accumulation cannot recover probabilities already rounded to zero.

## Risks

- Explicit sharing can keep a full score tile live longer, increase UB pressure or spills, and force a smaller legal tile.
- Sentinel masking (`-65504` plus the selected all-masked-row handling) requires the sentinel to underflow in `exp`/`exp2` for every reachable `m_safe`; verify all-masked rows produce exactly 0 and no legitimate score range violates the bound.
- Reassociation, changed cast placement, or changed infinity/NaN behavior can violate the normalization contract.
- A source-level operation reduction may lower to identical IR or disturb Cube scheduling enough to regress total latency.
- Improvements can be shape-specific when boundary paths, occupancy, or score-tile sizes differ.
- FP16 probability rounding can erase small nonzero probabilities, especially for sharp score distributions, long sequences, or large scaling ranges.
- Moving the cast across `tl.exp` or using rounded probabilities in the denominator can change recurrence semantics rather than only PV lowering.

## Related Patterns

- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): delete invalid recurrence trips and peel mask-free valid tiles before optimizing remaining work.
- [dot-operand-precision-ablation](./dot_operand_precision_ablation.md): run the generic matched lower-precision dot operand experiment with fixed work and a validated fallback.
- [algebraic-optimization](./algebraic_optimization.md): handle general semantics-preserving math reformulations outside this mixed-engine serial path.
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): choose computation and storage boundaries.
- [normalization-base-convention-ablation](./normalization_base_convention_ablation.md): ablate complete natural-base and base-2 normalization conventions.
- [cv-intermediate-tile-orientation](./cv_intermediate_tile_orientation.md): choose `[M, N]` versus `[N, M]` for the Cube-to-Vector score tile before shortening Vector work on that tile.
- [现有知识：Attention 优化经验聚合](../experiences/attention_experiences.md)
- [现有知识：CV 融合方法论](../operator_optimization/cv_fusion.md)

## What To Verify After Applying

- Correctness across representative dtypes, causal/noncausal masks, ragged and aligned/unaligned boundaries, plus NaN/inf behavior required by the operator.
- Profile evidence that the targeted Vector interval or wait is reduced and that total-operation latency improves.
- IR evidence that the duplicate or sequential chain was removed rather than silently rematerialized.
- Compiler-reported UB, spills, legal tile sizes, Cube scheduling, and the unchanged recurrence-trip count and transferred-byte baseline.
- Benchmarks across important shapes; reject or gate candidates that only move cost or regress boundary paths.
- For PV precision candidates, use `dot-operand-precision-ablation` and additionally hold masks, recurrence convention, denominator semantics, exponential convention, and output placement fixed.
- Validate extreme score ranges, tiny nonzero probabilities, multiple sequence lengths and scales, causal/noncausal modes, prefix 0/full/aligned/unaligned regimes, tails, and unequal Q/KV lengths where supported.
- Prefer an independent high-precision reference and record error summaries, finite/NaN/Inf behavior, repeated timing stability, selected lowering, and the FP32 fallback boundary.
