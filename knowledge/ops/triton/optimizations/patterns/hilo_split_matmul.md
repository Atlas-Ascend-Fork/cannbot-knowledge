---
type: Optimization
title: Hi/Lo Split Matmul (Split2 / Split3)
description: 用取整 fp16 高位与残差部分逼近 fp32 操作数，以两到三个原生 fp16 tl.dot 组合出 fp32 累加结果。
tags: [task.optimization, topic.precision, topic.compute.composite]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/hilo-split-matmul.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Hi/Lo Split Matmul (Split2 / Split3)

## Summary

Approximate fp32 operands with rounded fp16 high and residual parts, then combine two or three native fp16 `tl.dot`s into an fp32 accumulator. This can keep a larger tile on the fp16 MMA path, but the residual is rounded and the result is valid only for a tested value range and accuracy contract.

## Use When

One of two situations:

- **fp32 dot hotspot**: a contraction that must keep fp32 accuracy is the
  hotspot, and it runs one fp32 `tl.dot` (`acc = tl.dot(p, v, acc)`) whose
  fp32 operands take so much UB that the tile is capped well below the size
  the fp16 path could use.
- **Post-rewrite accuracy gap**: a structural rewrite (split-K, axis split,
  head batching, online-softmax regrouping) changed the summation order, and
  the accuracy gate now fails by about 1 ulp — the reference computes in
  fp32, but the kernel needs to stay on the fast fp16/bf16 dot path and naive
  low-precision rounding no longer passes.

In both, typically only one operand needs the split because the other is
already exactly representable in fp16/bf16.

The split replaces one fp32 dot with two or three fp16 dots, so it pays only
when the larger fp16 tile or the accuracy repair outweighs the extra dots.

## Avoid When

- The fp16/fp32 MMA rate advantage on the exact tile sizes is smaller than the
  dot multiplier: when the fp16 dots run on the same small tile the fp32 dot
  used, the change is neutral-to-negative, and the win only appears with
  fp16-sized tiles. This scopes the standalone equal-tile probe; it must not
  be used to reject the compensated form when that form is being landed as a
  flow enabler for a tile-fit re-scan or a split.
- The second operand is fp32 and correctness-sensitive PV/probability math:
  fp32 split PV can fail systematically from register pressure and compile
  fit, so keep fp32 PV on the fp32 dot unless the operator's own audit says
  otherwise.
- A single fp16 dot would already be reference-exact (native fp16/bf16 inputs
  with exact products): prefer the single native dot over a split.

## Method

Confirm the pattern applies first: profiling shows the contraction pinned at
the fp32 Cube rate, and an fp16 dot on the same shape would run at a larger
tile. Check each operand's precision surface — an operand already exactly
representable in fp16/bf16 needs no split at all.

The optimization core is to replace the fp32 dot with two or three native
low-precision dots over a rounded high part and a residual part, accumulated
in fp32, and to size the tile up to what the smaller operand footprint now
allows.

Discipline note: when an operator flow requires this compensated layer before
a tile-fit re-scan or a reduction-axis split, land it directly even when an
equal-tile probe shows no gain; its value is measured at those later stages.

### Rule: Choose split depth from operand dtypes

- split2 (fp32 x fp16-exact): use two fp16 dots for the rounded high and
  residual parts; the error estimate depends on residual rounding, scaling,
  range, and cancellation.
- split3 (fp32 x fp32): use the high-high and two cross terms when the omitted
  low-low term is within the tested error budget; do not treat the estimate as
  an unconditional bound.

### Rule: Pick fp16 versus bf16 by operand range first

When the fp32 operands span fp32 range (magnitudes above the fp16 max, or tiny
values fp16 flushes), split into two bf16 values instead: `x = x_hi + x_lo`
with RNE bf16 hi and a bf16 residual lo, computed with two or three bf16
`tl.dot`s and an fp32 accumulator.

- The precision budget is fundamentally coarser than the fp16 split: bf16
  hi+lo represents ~16 mantissa bits, so per-product error is ~2^-16 (vs
  ~2^-22 for fp16 split2/3). The dropped `lo*lo` term (~2^-32) remains
  negligible.
- The speed win is real but modest and applies only to cube-bound fp32
  contractions: the fp32 path is replaced by a small number of lower-precision
  MMA passes, so memory-bound or transfer-dominated stages gain nothing.
- Audit gate feasibility per output path, not per dot. A bf16-split dot
  feeding an exp/softmax front path can exceed a tight end-to-end gate even
  though the per-dot error is ~2^-16, because downstream exponentiation
  amplifies it. Paths with looser gates (or whose downstream is Lipschitz-1)
  pass.

Choose between the fp16 and bf16 splits on operand range first (bf16 keeps
fp32-like exponent range), on the gate second (fp16 split is far more
accurate where its range holds).

### Rule: Compute the hi/lo pair with the magic-constant recipe

```python
p_hi32 = (p + 65536.0) - 65536.0      # RNE-round p to fp16 precision in fp32
p_hi = p_hi32.to(tl.float16)
p_lo = (p - p_hi32).to(tl.float16)
pv = tl.dot(p_hi, v, acc_hi) + tl.dot(p_lo, v, acc_lo)
```

Scaling the residual before rounding (for example
`p_lo = fp16((p - p_hi) * 2048)` with a matching `1/2048` factor on the second
dot) extends the usable residual range. A subtraction-to-bf16 split
(`hi = bf16(p); lo = bf16(p - hi)`) gives no accuracy improvement over the
fp16 magic-constant split; re-derive through IR per operator before
generalizing either result.

Cache the hi/lo pair on the full weight object before any column slicing: a
slice creates fresh tensor objects and silently re-splits or misaligns.

### Rule: Keep independent fp32 accumulators per dot

Sum the per-dot accumulators at the store; chaining the dots into one
accumulator can hit compiler miscompile/lowering issues. Even with
independent accumulators, a multi-descriptor two-pass split can miscompile
nondeterministically (identical inputs, run-to-run diffs,
num_stages-independent), so split-K dots are currently safe only in
single-pass or plain GEMM kernels; verify determinism before relying on a
split-K form.

### Rule: Count the tile unlock as part of the win

The fp16 operand footprint is half of fp32, which lowers the UB planner
requirement and is often what makes a larger BLOCK_N/BLOCK_K fit where the
fp32-direct tile overflowed UB. Precision budget still matters: error ~2^-22
per product is far inside a 1e-2/2% differential gate, but keep a validated
fp32 fallback for exactness-critical paths.

### Rule: On attention PV, repair precision in ladder order

1. Keep the softmax probabilities `p` in fp32; do not round them to bf16/fp16
   before PV.
2. If fp32 `tl.dot` is unsupported or falls off the Cube path, split only `p`
   with the recipe above.
3. Keep partial `(acc, max, sum)` state in fp32 across split/combine.
4. Only after this passes correctness, tune split depth or tile geometry.

When results drift, check the rounding point, not just the dot: a store or a
following recurrence may round intermediates the reference kept at a specific
place. Reproduce that rounding with a Veltkamp RNE emulation in pure fp32 when
register `.to(dtype).to(fp32)` casts are compiler-folded.

Do not generalize GEMM probe results to attention: fp32 split-PV GEMM probes
can fail systematically from register pressure and compile fit, while the same
two-dot `p_hi/p_lo` PV in an attention path with fp32 `p` and fp16 `V` can
pass the MERE gate and be required for split/combine correctness. Audit per
operator instead of banning the split globally.

Host-side pre-cast of the second operand (V) is a shape-gated decision, not a
default: it only pays when the in-kernel cast is redundant across consumer
programs. Redundancy ~ `head_blocks * S_q * topK / S_kv`; when that ratio is
near 1 the fixed cast cost dominates and the change regresses, while a large
ratio makes it pay. Keep the in-kernel cast for small-`S_q` regimes and cache
the cast buffer when it is hoisted to the host.

## Signals

### Profile

- fp32 cube utilization pins a GEMM-heavy path at the fp32 MMA rate while fp16
  GEMM probes on the same shapes run several times faster.

### Code

- An fp32 `tl.dot` whose tile is capped much smaller than the fp16 tile the
  same shape could use.

## Related Patterns

- [dot-operand-precision-ablation](./dot_operand_precision_ablation.md): run the generic lower-precision operand ablation;
  this card is the hi/lo compensation mechanism that makes it exact enough for
  fp32 semantics.
- [reduction-axis-split-combine](./reduction_axis_split_combine.md): when a split passes algebra but fails
  MERE at ~1 ulp, use this card for the per-slice PV rather than tuning split
  depth blindly.
- [gather-then-dense-compute](../operator_optimization/device_side_gather.md) / [dense-substitution-fine-grained-sparse-attention](./dense_substitution_fine_grained_sparse_attention.md):
  densify and mask regrouping change probability rounding points; route a
  MERE-edge failure through the repair ladder above.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): the tile unlock is often the enabling
  mechanism.
- [attention-online-softmax-fusion](./attention_online_softmax_fusion.md): its native-dtype rounding variant carries the
  scores/weights rounding repair notes that apply when the split feeds a
  fused attention path.

## What To Verify After Applying

- Differential correctness on every dtype and shape family, especially large
  magnitudes where the dropped `lo*lo` term could approach the tolerance.
- Per-case differential on the correctness-sensitive PV/probability paths
  before promoting the split.
- The dots actually run on the fp16 MMA path at fp16 tile sizes (measure TMAC/s
  and compare against the fp32-direct baseline on the same shape).
- Independent accumulators, cache-before-slice, and the fp32 fallback all
  survive regression.
