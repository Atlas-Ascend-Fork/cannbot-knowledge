---
type: Optimization
title: Dense Substitution For Fine-Grained Sparse Attention
description: 当逐行任意索引选取的 KV 占比足够高时，用带散射 mask 的稠密计算替代细粒度稀疏 attention 选取。
tags: [task.optimization, topic.attention, topic.compute.indexing]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/dense-substitution-fine-grained-sparse-attention.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Dense Substitution For Fine-Grained Sparse Attention

## Summary

When an attention operator selects KV positions by per-row arbitrary indices
(topK sparseIndices, DSA/MLA style) and the selected fraction `topK / S_kv`
is not tiny, replace gather-based sparse compute with a dense pass over the
full `S_kv` plus a scattered boolean mask. Dense runs entirely on contiguous
loads feeding `tl.dot` at cube rate. A gather whose rows are masked or
non-contiguous can incur many small indirect row loads or an extra workspace
GM round trip. A mask-free, row-contiguous gather can avoid much of that cost,
so measure that in-place fix before paying the dense FLOP multiplier.

## Use When

An attention operator selects KV positions by per-row arbitrary indices
(`indices[b, h, s, topK]`, no block structure), and profiling shows the
sparse path dominated by gather traffic — many small random-row loads, or a
separate gather pass that writes the selected K/V rows to memory and reads
them back. The idea: when the selected fraction is not tiny, computing
densely over the full `S_kv` at full cube rate plus a boolean mask can beat
fewer but random reads. Start testing around `topK / S_kv >= 1/8`, then
remeasure the crossover across `S_q`, `D`, dtype, and loader form;
`topK * 8 >= S_kv` is not a portable dispatch rule.

Two gates before substituting. First, the cheap loader repair has been tried
and rejected: if rewriting the gather so each key row loads as one contiguous
chunk without a data-dependent mask turns it into block transfers, fix the
load form and stop there. Second, the dense-mask form must be legal: the
`[B, H_kv, S_q, S_kv]` bool/int8 mask fits memory and can be built by one
scatter kernel, and per-row indices are unique (a boolean mask cannot count a
duplicated index twice).

## Decision Boundary (vs gather-densification)

Three branches, not two. Compare in this order:

- keep the gather and fix its lowering: drop the data-dependent row mask
  (clamp invalid rows, re-mask the scores) and load each key row as one
  contiguous chunk. This is the cheapest branch and it frequently removes the
  whole penalty, with no dense pass and no materialised workspace.
- dense: read full `S_kv` once + build/apply a `[S_q, S_kv]` mask (its cost scales with S_q * S_kv); FLOP multiplier `S_kv / topK` on the dot.
- densify: read `topK` rows once + write/read a `[rows, topK, D]` buffer; dot over `topK` only; requires index spread (same-address hot spots serialize the pass).

Dense wins when `S_kv / topK` is small relative to the residual gather-path
inefficiency AND the mask cost is affordable at large `S_q`. Densify wins when
`S_q` is large enough that the mask matrix dominates, or the buffer fits
cache/stream well - but both alternatives can lose to the loader repair when
the source operand is cache-resident and the gather is already row-contiguous.
Measure all three branches at the operator's real shape regime before
committing; the boundary moves with S_q, topK, D, and dtype.

## Avoid When

- `topK / S_kv` is very small or `S_q` is tiny (decode/MTP): the dense FLOP
  multiplier exceeds the gather cost; keep the gather+dot path.
- Indices are block-aligned or clustered: a block-sparse kernel (BlockMask
  style) may delete whole tiles and can be a better candidate, but compare setup, occupancy, and end-to-end latency before choosing it.
- The toolchain supports feeding row-gathered tiles to `tl.dot` at cube
  rate (e.g. via a native gather-to-L1 intrinsic); then true sparse wins.
- The contract pins per-occurrence quantization of duplicated indices. A
  boolean or count mask collapses duplicates, and neither `log(count)` bias nor
  post-quantization count weighting reproduces "each occurrence quantized once,
  then accumulated" bit-for-bit; it can leave bf16 output elements one ulp off
  and fail matched_ratio. Materialize the duplicates instead
  (`repeated-gather-compute-once` only applies to block-level
  multiplicity where the count compensation is exact).

## Signals

### Code
- A separate gather kernel writes a full-problem `K_sel` workspace, or a
  fused kernel issues per-row indirect loads in the attention loop.
### Profile
- Gather effective bandwidth far below HBM peak for narrow rows; workspace
  write+read at gigabyte scale per call.
- In-place-fix signal (prefer the loader repair, not a dense pass):
  Vector-dominant engine balance with an idle DMA path - `aiv_vec_ratio`
  0.85-0.95, `aic_mte2_ratio` < 0.05, roughly one issue per loaded element,
  and cost scaling with staged elements x KV trips. That profile means the
  gather lowering is the wall; dropping the row mask and widening the row load
  addresses it directly.
### Math
- Block-level sparsification is provably useless: for random density `d`,
  a block of 16 positions is touched with probability `1-(1-d)^16`
  (d=1/8 -> 88%), so no block-sparse tiling can recover the `1/d` FLOP
  saving; only row-granular gather+dot can, which Triton cannot express.

## Related Patterns

- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md) (opposite direction: delete provably invalid
  tiles; use it when visibility is block-structured instead of random)
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md) (host discriminator for dense vs
  gather path)
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md) (mask scatter is the cheap
  materialization; the expensive K_sel one is what gets eliminated)
- [现有知识：Attention 优化经验聚合](../experiences/attention_experiences.md)

## What To Verify After Applying

- MERE/MARE on every shape, especially all-masked rows (must produce 0).
- Mask build cost (zeros + scatter) is included in the measurement; byte
  scatter is cache-line transaction bound and is not tunable by block size.
- The dense path does not regress shapes the discriminator routes to it;
  keep the gather fallback for small `S_q` and small `topK / S_kv`.
- Failure routing: if the dense/regrouped path fails MERE/matched_ratio at
  about 1 ulp under a pure-fp32 reference, re-sync mask/expansion/quantization
  semantics first, then use `hilo-split-matmul` for the fp32
  probability PV path.
