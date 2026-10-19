---
type: Optimization
title: Contract-Gated Dot Operand Precision Ablation
description: 在合约门控下独立消融 tl.dot 操作数的低精度形态，与累加器、递推、epilogue 和输出精度解耦评估。
tags: [task.optimization, topic.precision, topic.compute.quantization]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/dot-operand-precision-ablation.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Contract-Gated Dot Operand Precision Ablation

## Summary

Ablate matched lower-precision `tl.dot` operands independently from accumulator, recurrence or epilogue, and output precision. Treat the lower-precision path as a measured, contract-gated candidate with a validated fallback, never as a default rewrite.

## Use When

Your kernel feeds a `tl.dot` (or equivalent Cube operation) with matched FP32
operands, either because the operands are stored as FP32 or because
lower-precision source tiles are upcast only to feed the dot:

```python
left_dot = left.to(tl.float32)   # source tile is fp16/bf16
right_dot = right.to(tl.float32)
acc = tl.dot(left_dot, right_dot, acc=acc_fp32)
```

The target supports a higher-throughput matched lower-precision operand pair
with a higher-precision accumulator. The operator's accuracy contract permits
a controlled operand-rounding experiment, and representative correctness
cases are available. Tile geometry, grid, logical work, and surrounding
arithmetic can stay fixed, so operand precision is independently
attributable.

## Avoid When

- The public contract, reference algorithm, or required tolerance mandates the original operand precision.
- Inputs contain values whose range or small nonzero magnitude cannot survive the proposed format and no guarded fallback can be retained.
- The candidate also changes reduction order, tile coverage, algorithm, recurrence state, output placement, or another major variable that cannot be isolated.
- The target/compiler does not support the proposed operand pair or lowers both candidates to the same effective path.

## Signals

### Code

- FP16/BF16 source tiles are converted to FP32 only to feed a dot whose accumulator is already FP32.
- A generated FP32 intermediate feeds a dot but can be rounded at a semantically explicit boundary.
- Dot operand precision, accumulator precision, and final store precision are coupled in one expression or assumed to be identical.

### Profile

- A Cube/matrix-compute stage is significant, and matched lower-precision operands could select a higher-throughput implementation.
- An equal-work operand-precision control changes kernel latency without changing launches, recurrence iterations, or transferred logical bytes.
- Performance differs by shape or dtype enough to justify a guarded dispatch rather than one universal path.

### IR

- The lower-precision candidate selects a different dot/Cube lowering while accumulator and surrounding arithmetic remain unchanged.
- Operand rounding shortens live ranges or lowers UB pressure, but the claimed benefit is separated from any change in which tiles fit.

## Method

Confirm the fit first: code or IR shows the FP32 conversion immediately
before the dot, the profile shows a significant Cube/matrix-compute stage,
and tile geometry, grid, reduction order, and surrounding arithmetic can be
frozen. Record the precision decomposition below as the fixed control
baseline.

The optimization core is to run the direct matched lower-precision operand
candidate at equal work. Only when it misses the accuracy contract but
lowering evidence justifies continuing, climb the compensated high/low
decomposition ladder. Build one candidate at a time; do not combine it with
tile changes, reduction-order changes, accumulator changes, or output-precision
changes. Promote the cheapest candidate that passes the full accuracy
contract and repeated benchmark comparison, and keep the original precision
path as the fallback for every unvalidated regime.

### Rule: Record the precision decomposition before editing

Record these choices separately before editing:

1. left dot operand dtype and rounding location;
2. right dot operand dtype and rounding location;
3. dot accumulator dtype;
4. reduction, recurrence, or epilogue state dtype;
5. kernel output dtype;
6. public output conversion and where the output is written to memory.

A lower-precision operand experiment does not imply a lower-precision
accumulator or output. Keep the accumulator and surrounding state at the
parent precision unless they are tested in separate candidates.

### Candidate: Direct matched lower-precision operands

Compare matched operand pairs while holding work and surrounding precision
fixed:

```diff
- left_dot = left.to(tl.float32)
- right_dot = right.to(tl.float32)
- acc = tl.dot(left_dot, right_dot, acc=acc_fp32)
+ left_dot = left.to(tl.float16)
+ right_dot = right.to(tl.float16)
+ acc = tl.dot(left_dot, right_dot, acc=acc_fp32)
```

Use the lower-precision format supported by the target and justified by the
source range; FP16 above is an experiment value, not a universal choice. Keep
the operand dtypes matched unless target documentation and a validated
existing pattern support a mixed pair.

Freeze tile sizes, grid, masks, loop bounds, reduction order, algorithm,
input data, output placement, and benchmark contract. If lower precision also
unlocks a larger tile, first run the equal-tile control here, then use
`large-tile-fit-enabling` to attribute the combined tile-fit effect.

When possible, run a bidirectional control: lower the parent operands and
restore higher-precision operands in the optimized structure. This catches
gains incorrectly attributed to operand precision when loop, layout, or
scheduling changes are responsible.

### Candidate: Compensated high/low decomposition ladder

A higher-precision accumulator does not compensate for information lost while
rounding dot operands. When lowering evidence or a non-canonical directional
screen justifies continuing but the direct lower-precision candidate misses
the accuracy contract, test explicit high/low decomposition before rejecting
that path.

For FP32 parent operands and a selected lower-precision dot dtype, construct
rounded high parts and rounded residual parts at an explicit boundary:

```python
left_hi = left.to(tl.float16)
left_lo = (left - left_hi.to(tl.float32)).to(tl.float16)
right_hi = right.to(tl.float16)
right_lo = (right - right_hi.to(tl.float32)).to(tl.float16)
```

FP16 is an experiment value here; use a target-supported format justified by
range and lowering evidence. Accumulate every candidate in the recorded
parent accumulator dtype. Compare this ladder:

| Candidate | Retained products |
| --- | --- |
| One product | `hi*hi` |
| One-sided, two products | `hi*hi + lo*hi`, or `hi*hi + hi*lo` — test each side separately |
| Two-sided, three products | `hi*hi + lo*hi + hi*lo` (omits `lo*lo`) |
| Two-sided, four products | all four products |

The two sides need not have the same error distribution or reuse cost. The
three-product candidate is approximate because it omits the low-low term, and
the four-product candidate still cannot reconstruct bits lost when the
residual parts themselves are rounded; neither is automatically equivalent to
the parent FP32 dot or its accumulation order.

Keep tile geometry, grid, masks, loop bounds, output placement, input data,
HF32 controls, and other global math-mode flags fixed across the ladder. The
number of dots is the intentional variable. Test left-only and right-only
compensation independently before attributing a result to two-sided
compensation.

Account for decomposition and reuse explicitly. Prefer tile-local
decomposition when writing high/low tensors to GM would erase the Cube gain.
If a repeated operand is decomposed or cached outside the kernel, include
that work in the selected metric and invalidate cached parts on storage,
dtype, device, layout, or value mutation as required by the public contract.

### Rule: Gate on the accuracy contract and keep a validated fallback

Lower-precision operands round before multiplication; a higher-precision
accumulator cannot recover information already rounded away, and compensated
candidates recover only the residual terms they explicitly retain. Validate
ranges, cancellation, small nonzero values, overflow/underflow, NaN/Inf
behavior, boundary shapes, and every supported dtype regime against an
independent high-precision reference where practical.

Retain a candidate only when the actual accuracy contract passes and repeated
benchmark improvement is stable. If only some shapes, dtypes, value ranges,
or semantic regimes pass, keep the original path as a guarded fallback and
dispatch only on conditions proven by tests. Do not infer runtime value
safety from benchmark inputs unless the public contract provides the needed
bound.

## Attention PV Specialization

For online attention PV, the generic experiment becomes matched FP32 P/V versus matched lower-precision P/V with FP32 max, denominator, recurrence scaling, and accumulator. Probability cast location and denominator semantics are additional attention-specific variables: casting the exponent input, casting the `exp` result, and summing rounded versus unrounded probabilities are not equivalent. Use `attention-intermediate-vector-work-reduction` for those boundaries and validate sharp distributions and tiny probabilities explicitly.

## Related Patterns

- [algebraic-optimization](./algebraic_optimization.md): keep reassociation and operand precision as separate
  experiments, then validate their composed rounding boundaries.
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md): retain the parent precision or
  accumulation order outside the semantic regimes proven safe.
- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): apply attention-specific probability, recurrence, and cast-location checks around a PV precision candidate.
- [dot-matmul-rewrite](./dot_matmul_rewrite.md): establish the regular tiled dot structure and a supported accumulator baseline.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): separate an equal-tile operand-precision gain from a larger tile enabled by the precision change.
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): test kernel-output precision and external casts independently from dot operand precision.
- [autotune](../operator_optimization/autotune.md): dispatch or tune validated operand-precision paths by shape without mixing correctness gates.
- [现有知识：混合精度与精度验证](../techniques/data_type_precision.md)
- [现有知识：matmul 链中间 buffer dtype](../operator_optimization/chained_matmul_buffer_dtype.md)

## What To Verify After Applying

- Both dot operands use the intended supported dtype and the accumulator remains at the recorded precision.
- Parent and direct lower-precision candidate have identical logical work, tile, grid, reduction order, surrounding state, and output placement; compensated candidates separately record their additional dots and combination order.
- Compensated candidates record the high/residual rounding boundary, retained cross terms, omitted terms, decomposition placement, and cache invalidation contract.
- HF32 controls and other global math-mode flags remain fixed across the operand-precision and compensation comparisons.
- Correctness covers representative shapes, boundary regimes, value ranges, cancellation, small magnitudes, overflow/underflow, and NaN/Inf semantics required by the operator.
- Repeated benchmarks show a stable improvement; noisy point estimates are not promoted.
- IR or compiler evidence confirms the intended dot lowering rather than an unrelated code-generation change.
- Every rejected regime has the original validated precision path or another explicit fallback.
