---
type: Optimization
title: Normalization Base Convention Ablation
description: 把自然底与 base-2 两套完整指数归一化实现作为整体约定消融，保持标量数学与向量路径语义一致。
tags: [task.optimization, topic.compute.normalization, topic.precision]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/normalization-base-convention-ablation.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Normalization Base Convention Ablation

## Summary

Ablate complete natural-base (`exp`/`log`) and base-2 (`exp2`/`log2`) implementations of exponential normalization as coherent conventions. Keep scaling, recurrence formulas, saved state, backward reconstruction, and all fast and boundary paths in the same convention.

## Use When

The kernel normalizes with exponentials over a recurrence with saved state —
online softmax, log-sum-exp, or similar — and profile or IR shows the
exponential instructions plus the base-conversion multiply chain on the
critical path. A typical example — `exp2` fed by scores carrying a `log2(e)`
factor:

```python
scores_2 = scores * scale * LOG2_E   # literal near 1.442695
p = tl.exp2(scores_2 - m_new[:, None])
```

The logarithm base must be a purely internal choice: nothing outside the
kernel reads the saved normalization state expecting a particular base, and
you must be able to find and switch every path that touches it — forward,
backward, and the saved state. If you can only see one local `exp2` call and
cannot account for the rest, do not apply this pattern yet.

Switching the whole convention removes the base-conversion chain from the
critical path and runs the normalization on the cheaper exponential path.

## Avoid When

- Only a local `exp2` call looks suspicious but the full normalization state contract and consumers are unknown.
- The operator contract exposes a particular logarithm base or saved-state representation that cannot change.
- Exponential work is not material in profile/IR, or the likely issue is ordinary algebra, work deletion, or Cube/Vector scheduling.
- Correctness coverage cannot exercise backward and every fast/boundary path that reads or writes normalization state.

## Signals

### Code

- Trace the upstream dataflow of every `exp2` input rather than searching only for intrinsic names. Base conversion may appear as a literal near `1.442695`, a named `LOG2_E` or `INV_LN2`, division by a literal near `0.693147`, or an equivalent expression.
- The `log2(e)` factor may be fused into the score scale, applied to Q or K, or folded into a dot operand before the score tile exists; inspect producers far enough upstream to recover the effective scale reaching `exp2`.
- Scores or recurrence deltas use that effective base conversion before `exp2`, while normalization state is stored with `log2` or a base-2 recurrence.
- Forward and backward contain paired conversions whose sole purpose is maintaining one implementation base.
- Exact-tile, causal, ragged, or fallback paths spell the normalization recurrence separately and may drift between conventions.

### Profile

- Special-function instructions plus base-conversion multiplies occupy a meaningful part of the critical path.
- A controlled convention-only ablation changes latency while tile shape, recurrence iterations, precision, and work coverage stay fixed.
- Performance differs by shape or path, suggesting neither base should be selected globally without boundary measurements.

### IR

- Follow the upstream IR dataflow into `exp2`: the mathematical `log2(e)` factor may remain as a multiply/divide/conversion chain, be folded into a scale or Q/K/dot operand, or disappear at no incremental runtime cost.
- A literal approximation such as `1.442695` denotes a compile-time constant, not a runtime logarithm instruction. The potential extra runtime cost is the surviving base-conversion multiply, divide, cast, or conversion chain.
- Saved-state production and backward reconstruction lower through different bases or redundant conversion chains.
- Fast and boundary paths lower different special-function sequences for the same mathematical normalization.

## Method

Confirm the fit first: profile and IR must show the special-function and
base-conversion chain on the critical path, and every reader and writer of
normalization state must be inventoried so a complete switch is possible.

The optimization core is to treat each convention as one end-to-end contract
and measure the complete candidates against each other. A candidate covers
every exponential, logarithm, score scale, online-max delta, normalization
sum, saved log-sum-exp state, backward reconstruction formula, and every
exact-tile, masked, causal, ragged, fast, and boundary path.

### Rule: Convert the whole convention, not one intrinsic

The exact symbols vary by kernel, but the conversion must include recurrence
state and saved state rather than replacing one intrinsic:

```diff
- scores_2 = scores * scale * LOG2_E
- m_new_2 = tl.maximum(m_2, tl.max(scores_2, axis=1))
- alpha = tl.exp2(m_2 - m_new_2)
- probs = tl.exp2(scores_2 - m_new_2[:, None])
- l_new = l * alpha + tl.sum(probs, axis=1)
- saved_lse_2 = m_new_2 + tl.log2(l_new)
+scores_e = scores * scale
+m_new_e = tl.maximum(m_e, tl.max(scores_e, axis=1))
+alpha = tl.exp(m_e - m_new_e)
+probs = tl.exp(scores_e - m_new_e[:, None])
+l_new = l * alpha + tl.sum(probs, axis=1)
+saved_lse_e = m_new_e + tl.log(l_new)
```

Backward must then consume `saved_lse_e` and reconstruct probabilities in the
natural convention; every base-2 fast or boundary path must change with it.
Replacing only `tl.exp2(x)` with `tl.exp(x)` while leaving `x` scaled by
`LOG2_E`, or leaving saved LSE in base 2, changes the mathematics and can
silently corrupt gradients.

### Rule: Attribute gains to the surviving conversion chain, not the intrinsic

Inspect IR to determine whether the base-conversion multiply/divide chain
remains, is folded into a scale or Q/K/dot operand, or has no incremental
cost. A literal near `1.442695` is a compile-time constant; only a chain that
survives lowering is a runtime cost. Do not attribute a measured gain
automatically to the exponential intrinsic itself — another compiler may fold
or lower the same chain differently, so compare both complete conventions on
the actual target.

### Rule: Hold everything else fixed and isolate scale moves

Compare `exp2 + base-conversion path` against natural `exp` while holding
precision, tile shapes, recurrence iterations, masks, and work coverage
fixed. If a convention requires a scale move, record it and run an additional
ablation that separates the scale-move effect from the base effect:

| Candidate | Exponential | Saved state | Scale placement |
|---|---|---|---|
| base-2 | `exp2`/`log2` | base-2 LSE | `log2(e)` folded or separate |
| natural | `exp`/`log` | natural LSE | unchanged |
| natural + scale move | `exp`/`log` | natural LSE | moved (isolate this effect) |

Discipline note: run correctness before performance, then compare profile,
IR, and benchmark evidence per important path and shape. If special-function
IR is unchanged, the chain is not critical, or no candidate improves total
latency, record no benefit and pivot to the pattern matching the remaining
bottleneck.

## Risks

- A partial conversion can produce plausible forward values while saved state or backward gradients use the wrong base.
- Floating-point order, overflow/underflow thresholds, rounding, and tolerance can differ between mathematically equivalent conventions.
- Scale hoisting or precision changes can confound attribution and may be legal only for specific dtypes or exact constants.
- Different compiler or hardware versions may lower the same intrinsic differently; a winner can reverse across paths or shapes.

## Related Patterns

- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): reduce other serialized Vector transformations between Cube producer and consumer while holding the math convention fixed.
- [algebraic-optimization](./algebraic_optimization.md): handle identities not requiring a complete normalization-base state contract.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): remove invalid attention recurrence work without changing normalization convention.
- [现有知识：归一化优化经验聚合](../experiences/normalization_experiences.md)

## What To Verify After Applying

- Forward outputs, backward gradients, saved-state values and consumers against an independent reference across representative magnitudes and dtypes.
- Every fast and boundary path, including causal, noncausal, ragged, aligned/unaligned, short, and exact-tile cases.
- Finite behavior, NaN/inf propagation, overflow/underflow boundaries, and configured tolerances.
- Profile evidence for the special-function chain, IR evidence for the intended intrinsic and conversion sequence, and benchmarks for kernel and total-operation latency.
- Equal work, precision, tile configuration, recurrence iterations, and scale placement—or explicit separate attribution when one must differ.
- If there is no repeatable gain, retain the safer or established convention and pivot rather than forcing the change.
