---
type: Optimization
title: Attention Online Softmax Fusion
description: 把 QK、mask/softmax、PV 分阶段的 attention 合并为单 kernel 在线 softmax 递推，含 native-dtype 舍入复现的两遍形式。
tags: [task.optimization, topic.attention, topic.compute.normalization]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/attention-online-softmax-fusion.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Attention Online Softmax Fusion

## Summary

Replace a staged attention implementation — QK, masking/softmax, and value
aggregation as separate kernels that write score and probability tensors to
memory between stages — with one kernel whose programs each own a query tile
and run an online softmax recurrence over key tiles, so scores and
probabilities never leave on-chip state.

## Use When

One attention operator invocation runs as several separate kernels — a QK
matmul, a softmax, and a value-aggregation (PV) matmul visible as distinct
launches in the profile — and the score or probability tensors passed between
them exist only to connect the stages. Fusing the stages into one kernel must
be legal and worthwhile (that decision belongs to
`kernel-fusion-and-value-placement`); this card supplies the
attention-specific online-recurrence construction.

## Avoid When

- Scores, probabilities, or post-softmax values are externally visible, reused, mutated, or required at an observable rounding boundary that the recurrence does not reproduce (see the native-dtype rounding variant below for the reproduction technique).
- One program cannot legally own the output tile and recurrence state without cross-program communication, illegal tiles, spills, or destructive loss of parallelism.
- The staged path must stay as the fallback when precision, randomness, live-state footprint, program batches, or total measured latency rejects the recurrence.

## Signals

### Code

- Separate QK, masking or softmax, and value-aggregation launches exchange score or probability tensors that have no external user.

### Profile

- Score/probability allocation and GM writes or reloads contribute materially to the measured call.

## Constructing The Online Recurrence

After `kernel-fusion-and-value-placement` selects a legal grouping
candidate, replace the staged QK -> masked-softmax -> probability-times-value
chain with one kernel where each program owns a query tile and runs an online
softmax recurrence over the key tiles visible to it. This card owns the
attention-specific construction; the generic fusion card continues to own
whether the boundary should be crossed at all, including the
launch-coalescing and retained-boundary dispositions.

Skeleton — one program per query tile, recurrence over its visible key tiles:

```python
acc = tl.zeros(...); m_i = -inf; l_i = 0
for each visible key tile:                # loop domain: see notes below
    scores = tl.dot(q_tile, tl.trans(k_tile))
    m_new = tl.maximum(m_i, tl.max(scores, 1))
    p = tl.exp(scores - m_new)            # invisible lanes must contribute 0
    corr = tl.exp(m_i - m_new)            # rescale for the new running max
    l_i = l_i * corr + tl.sum(p, 1)
    acc = acc * corr + tl.dot(p, v_tile)
    m_i = m_new
out = acc / l_i
```

Construction notes, in skeleton order:

- **Visible key range** (the loop domain): for a query tile covering
  `[q_begin, q_end)`, derive the union of key positions visible to any row in
  the tile. A contiguous left/right window commonly has a band shaped like
  `k_begin = max(0, q_begin - left)` and `k_end = min(kv_length, q_end + right)`.
  For dense attention the union is the complete valid key range; otherwise
  adjust inclusivity, dilation, causal restrictions, block lists, ragged
  lengths, and coordinate offsets to the public policy. Tile-align the union
  outward, but retain the exact per-element predicate on partial first, last,
  diagonal, sequence-tail, or sparse blocks. To delete provably invisible
  tiles from the loop domain, use `attention-visibility-mask-specialization`.
- **State and numerics** (`m_i`, `l_i`, `acc` in the skeleton): carry the
  running maximum, denominator, and value accumulator in FP32. Every visited
  tile updates with masked probability zero on invisible lanes. A row with no
  visible lane in a visited tile must keep its prior state unchanged: avoid
  the undefined all-masked `-inf - -inf` path by using zero probability, a
  unit correction, and a safe maximum update.
- **Padding is not visibility**: physical padding may make Q/K/V addresses
  exact, but it does not make padded keys semantically visible. A zero key
  score can still contribute `exp(0)`, and `0 * NaN` can contaminate a value
  dot, so retain logical validity and initialize every physically loadable
  padded lane.
- **Operand feeding** (the loads inside the loop): feed q/k/v tiles as
  descriptor loads per `block-pointer-tiles`; masked per-row SIMT
  gathers measure far slower and erase the fusion gain. Strided or subsampled
  layouts are not an excuse for SIMT — decompose them into affine
  residue-class views first (see that card).
- **Keep the staged fallback**: retain the staged path when precision,
  randomness, live-state footprint, program batches, or total measured latency
  rejects the recurrence.

## Variant: Native-Dtype Rounding Reproduction (fp16/bf16 Contract)

When the reference stores scores or probabilities in fp16/bf16 without an fp32 upcast, an online recurrence must reproduce the reference's rounding points. Do not assume that an in-register cast or a Veltkamp split is bit-equivalent for every finite value: range limits, subnormals, NaNs, signed zero, and compiler folding all matter. Scope any emulation to a verified compiler and value range, and keep the stored-reference path as a fallback when exact reproduction is not established.

- Reproduce EVERY rounding point: `RNE(matmul store)`, then `RNE(scores / sqrt(hd))` — two separate roundings; emulating only one (`dot * reciprocal`) leaves the div-vs-mul 1-ulp difference, which the same amplification blows past the gate. Then `RNE(softmax weights)` — the NORMALIZED probability, not raw `exp(s - m)` (rounding unnormalized per-tile exps collapses small probabilities and corrupts the denominator).
- The weight-rounding point is unreachable in a single-pass online recurrence (the final denominator is known only after the last tile), so native contracts need a two-pass form: pass 1 derives the final per-row max/sum (QK only, no V traffic), pass 2 recomputes each score tile, normalizes, rounds the weight to the reference dtype, then runs PV. The doubled QK/exp work is the price; keep the staged chain as fallback for shapes where it loses.
- A compiler may fold an in-register cast away. Inspect the generated IR and compare against an independent cast reference before replacing it with arithmetic emulation.
- If a Veltkamp split is used, apply it BEFORE any `-inf` masking (`Veltkamp(-inf) = NaN` poisons the row max/sum), and test finite normals, subnormals, infinities, NaNs, signed zero, and the operator's actual dtype contract.
- Small errors only for native-dtype references can indicate a missing rounding stage, but this signal is not a proof; check structure and value ranges before changing the recurrence.

## Related Patterns

- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): decide whether the measured QK-softmax-value boundaries should be crossed before applying this card's construction.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): prune invisible and fully valid key tiles inside the resulting recurrence when the visibility policy permits it.
- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): shorten the remaining serialized Cube producer -> Vector transformation -> Cube consumer path in the fused kernel.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): operand-feeding mechanism for the recurrence's q/k/v tiles; SIMT gathers erase the fusion gain.
- [normalization-base-convention-ablation](./normalization_base_convention_ablation.md): ablate complete natural-base and base-2 normalization conventions for the recurrence.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): evaluate a wider key tile together with precision or live-shape enablers.
- [现有知识：在线算法概念（running max/sum）](../techniques/online_algorithms.md)
- [现有知识：Attention 优化经验聚合](../experiences/attention_experiences.md)

## What To Verify After Applying

- Correctness across representative dtypes, causal/noncausal masks, ragged and aligned/unaligned boundaries, plus NaN/inf behavior required by the operator.
- Confirm deleted score/probability tensors have no external users and their allocations, stores, reloads, and launches disappear from the measured path.
- Compare fused, partially fused, and retained staged variants by total-operation latency across support-width, dtype, head-dimension, and program-batch regimes.
- Record target/compiler identity and test repeated runs for determinism; if a target-specific compiler failure or nondeterminism is found, keep its reproducer in a decision record and retain only the general fallback rule here.
