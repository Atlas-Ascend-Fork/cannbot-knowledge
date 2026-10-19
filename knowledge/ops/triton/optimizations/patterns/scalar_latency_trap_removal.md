---
type: Optimization
title: Scalar Latency Trap Removal Pattern
description: 移除阻塞 Vector 硬件利用率的标量化构造：多余标量控制流、循环携带指针递推、取模寻址、窄 mask 与向量路径上的 int64 运算。
tags: [task.optimization, topic.programming_model, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/scalar-latency-trap-removal.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Scalar Latency Trap Removal Pattern

## Summary

Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.

## Use When

Profiling shows high scalar/control overhead — a high `aiv_scalar_ratio`, or
vector time that the arithmetic in the source cannot explain — and IR shows
vector operations lowered as scalar loops. The hot path then contains
scalarizing constructs such as: shape constants passed as runtime args
instead of `tl.constexpr`, loop-carried pointer updates (`ptr += BLOCK_K`),
modulo (`%`) tail guards, a `tl.where` selecting one special lane, `int64`
index math that fits `int32`, `tl.cumsum`/`tl.associative_scan` scalar
fallbacks, or boundary masks an earlier `boundary_check` already covers.

Typical examples — the loop-carried pointer update and the modulo boundary
guard:

```python
for k in tl.range(0, K, BLOCK_K):
    ptr += BLOCK_K                          # loop-carried address dependency
    offs = (k + tl.arange(0, BLOCK)) % N    # modulo boundary guard
```

## Signals

### Profile

- Degraded vector lowering usually shows up as a high `aiv_scalar_ratio`, or as vector time that cannot be explained by the arithmetic the source performs.
- When a high `aiv_vec_ratio` coexists with idle Cube and MTE, inspect the instructions and addresses before routing to `mask-only-affine-addressing`. The same ratio can also come from ordinary elementwise or normalization work.

### IR

- Vector operations fall back to scalar loops, or masked loads lower to conditional whole-tile `linalg.fill` plus `memref.copy`.

## Method

Confirm the fit first: the profile shows a high scalar share and IR shows the
targeted expression lowered as scalar code. The optimization core is to
rewrite each scalarizing construct so the hot path lowers to vector code.
Apply the rules below one at a time, re-measure after each, and keep a rewrite
only if the scalar fallback is gone from IR and latency improves.

### Rule: Pass compile-time constants as `tl.constexpr`

Make compile-time constants explicit:

```python
@triton.jit
def kernel(x, y, N: tl.constexpr, BLOCK: tl.constexpr):
    offs = tl.arange(0, BLOCK)
    mask = offs < N
```

Prefer `tl.constexpr` for fixed sizes, strides, booleans, mode flags, and architecture-selected knobs. Do not make data-dependent runtime values constexpr.

### Rule: Derive loop addresses from a stable base

Avoid pointer updates that depend on the previous iteration:

```python
# Prefer this shape.
for i in tl.range(0, K, BLOCK_K):
    ptrs = base + (i + offs_k) * stride_k + offs_n
    vals = tl.load(ptrs, mask=(i + offs_k) < K)
```

This keeps each iteration's address computation derived from a stable base plus an explicit offset. It is especially useful when the loop iteration count is large enough for scalar scheduling to matter.

### Rule: Replace modulo boundary guards with masks

Apply this repair only when `%` is being used as a boundary guard for tail or edge handling. If removing `%` would change the kernel's intended index mapping, this repair does not apply.

```python
# Before: modulo wraps the tail back into range.
offs = (block_start + tl.arange(0, BLOCK)) % N
vals = tl.load(x + offs)

# After: mask guards the tail instead.
offs = block_start + tl.arange(0, BLOCK)
mask = offs < N
vals = tl.load(x + offs, mask=mask, other=0.0)
```

### Rule: Delete redundant per-lane address clamps

The full repair lives in `mask-only-affine-addressing`. When a per-lane `minimum`/`maximum` clamp exists only to keep masked boundary lanes in range, delete it and let the existing load/store predicate protect those lanes. That repair is bit-exact, needs no divisibility guard, and is usually the highest-yield item on this checklist, so check it first.

### Rule: Replace a single-lane `tl.where` with a targeted fix

When exactly one lane differs, consider replacing a whole-vector `tl.where` with a targeted extract/insert style repair. Only apply this when the one-position condition is proven by shape or index construction. If more than one lane can differ, keep the original vector conditional.

### Rule: Keep hot vector arithmetic in `int32`

If index or offset arithmetic is proven to stay within `[-2**31, 2**31 - 1]`, cast once near load or construction and keep the hot vector math in `int32`. Cast back only when the API or pointer expression truly requires it.

Do not use this for values that can overflow `int32`.

### Rule: Remove boundary-only masks already covered by earlier loads

If prior loads already zero-pad invalid rows or columns through `boundary_check`, later vector predicates may not need to repeat both row and column validity. Keep semantic masks, such as causal lower-triangle conditions, but remove boundary-only terms that no longer protect an unsafe value.

```python
# Before: row and column validity repeated in the final mask.
m_A = (o_t[:, None] > o_t[None, :]) & (m_t[:, None] & m_t)

# After: row out-of-bounds is already zero from boundary-checked inputs.
m_A = (o_t[:, None] > o_t[None, :]) & m_t[None, :]
```

Only apply this when invalid lanes cannot reintroduce nonzero, NaN, or unsafe pointer behavior between the protected load and the final mask/store.

### Rule: Split a long 1-D `tl.cumsum` across a 2-D tile

For a long one-dimensional `tl.cumsum`, consider reshaping to a two-dimensional tile so cumsum runs on shorter axes, then combine block-local prefix totals. Tune the split size because both axes trade off against each other and can affect UB pressure.

### Rule: Move the cumulative axis off the last position

If `tl.cumsum` or `tl.associative_scan` is on the last axis and the backend lowers it to scalar loops, transpose or swap axes so the cumulative axis is no longer last before scanning. If the output layout needs the original axis order, transpose back after the scan.

```python
# Before: last-axis cumsum can fall back to scalar lowering.
prefix = tl.cumsum(values, axis=1)

# After: move the cumulative axis off the last position to unlock vector lowering.
prefix = tl.trans(tl.cumsum(tl.trans(values), axis=0))
```

## Risks

- `tl.constexpr` changes specialization behavior and compile-cache cardinality.
- Removing a per-lane clamp is only safe when valid-lane addresses are unchanged and every invalid lane is protected by a load/store mask or a proven initialized physical layout.
- Removing `%` is only safe when masks preserve the original boundary semantics.
- Removing redundant boundary masks is only safe when earlier boundary-checked loads or stores still fully protect out-of-range access and invalid lanes have safe values.
- Int32 conversion is a semantic promise about value range.
- Cumsum decomposition must preserve prefix order exactly.
- Axis swaps for cumsum can introduce an explicit transpose pass; keep the temporary footprint within UB limits.

## Related Patterns

- [mask-only-affine-addressing](./mask_only_affine_addressing.md): the per-lane address clamp repair split out of this checklist; delete clamps from pointer expressions whose load or store already carries a boundary mask.
- [strided-layout-reduction](./strided_layout_reduction.md): Avoid implementing a non-last-dimension single-axis reduction by first doing `movedim(...).contiguous()` or an equivalent layout copy to memory.
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md): introduce and cost an initialized physical layout when repeated consumers need mask-free raw affine loads.
- [现有知识：标量降级规避](../techniques/scalar_degradation_avoidance.md)
- [现有知识：Scalar 转 Vector 优化](../operator_optimization/scalar_to_vector.md)

## What To Verify After Applying

- Record the trap and exact code location in `attempts.md`.
- Run correctness before trusting performance.
- Use the project benchmark and `compare-perf` authority for any claimed speedup.
- If the repair changes specialization keys or host call signatures, verify all call sites.
