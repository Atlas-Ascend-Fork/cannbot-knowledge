---
type: Optimization
title: i64/i32 Comparison Optimization Pattern
description: 把显式整数比较密集逻辑改写为 Ascend NPU 上更向量友好的形式，尤其当标量化比较阻塞快速掩码或选择时。
tags: [task.optimization, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/vec-cmp.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# i64/i32 Comparison Optimization Pattern

## Summary

Rewrite explicit integer compare-heavy logic into a form that is more vector-friendly on Ascend NPU, especially when scalarized compares are blocking fast masking or selection.

## Use When

Your kernel computes an explicit `i64` or `i32` comparison into a named
boolean value, and that boolean feeds `tl.where`, a conditional assignment,
or a precomputed `mask=` variable on the hot path:

```python
mask = offsets < n_elements              # i64 compare, computed explicitly
x = tl.load(x_ptr + offsets, mask=mask)  # or: tl.where(mask, a, b)
```

The generated IR shows this integer compare lowered to scalar work. The
compare is not written inline as the `mask=` argument of a `tl.load` or
`tl.store`, where the compiler already applies its fast path.

## Signals

### Code

- An integer comparison produces a named boolean mask used in `tl.where`, conditional assignments, or a separately computed `mask=` variable.
- The code compares integer operands directly even though an exactly-representable `fp32` comparison would preserve the result.

### IR

- The integer compare lowers to scalar instructions rather than vector compare operations.

## Problem Description

On some Ascend compiler paths, explicit integer comparisons lower to scalar work and block vectorized masking or selection. Confirm the scalar lowering in the generated IR before changing the comparison form.

## Method

Confirm the fit first: the generated IR must show the integer compare as
scalar work on the hot path, and the compare must sit outside the compiler's
fast-path `mask=` handling.

The optimization core is to rewrite that one comparison so it lowers to
vector work, usually by casting both operands to `fp32`, and only when the
integer range is exactly representable. Skip comparisons already in `fp32`
or already vectorized contexts.

### Rule: Cast both compare operands to fp32 when the range is exactly representable

Cast both operands to `fp32` before the comparison only when every reachable
value is exactly representable, so the comparison result is unchanged. A
sufficient bound is both operands in `[-2^24, 2^24]` unless a stronger proof
is available:

```diff
- mask = offsets < n_elements
- x = tl.load(x_ptr + offsets, mask=mask)
+ offsets_f32 = tl.cast(offsets, tl.float32)
+ n_elements_f32 = tl.cast(n_elements, tl.float32)
+ mask = offsets_f32 < n_elements_f32
+ x = tl.load(x_ptr + offsets, mask=mask)
```

If the range proof does not hold, keep the integer comparison or use a
supported integer vector compare instead.

### Rule: Leave inline load/store mask arguments alone

A comparison written directly as the `mask=` argument, such as
`tl.load(x_ptr + offsets, mask=offsets < n_elements)`, is already handled by
the compiler's fast path. Converting it adds nothing. Only target compares
computed into a named boolean that is then consumed elsewhere.

### Rule: Treat compare-helper NaN propagation as an explicit choice

When hot-path compare helpers such as `tl.maximum()` or `tl.minimum()`
appear in the kernel, inspect similar call sites for omitted
`propagate_nan`. Add `propagate_nan=tl.PropagateNan.ALL` only when the round
intentionally wants explicit, consistent NaN propagation, and record it as a
semantics change for NaN inputs.

## Avoid When

- The comparison is an inline `tl.load`/`tl.store` mask argument; the compiler already optimizes it.
- The comparison is already in `fp32` or in an auto-vectorized context.
- The integer range exceeds the exactly-representable `fp32` bound and no stronger proof is available.
- The comparison is not performance-critical.

## What To Verify After Applying

- Verify the comparison result still feeds the same hot-path conditional logic after the dtype rewrite.
- Verify both operands are cast in a way that preserves semantic equivalence for the downstream mask usage.
- Re-check downstream dtype expectations and confirm in the generated IR that the comparison is no longer scalarized.
- Re-check `tl.maximum()` and `tl.minimum()` call sites on the hot path and document any intentional `propagate_nan` choice as a semantics change.
