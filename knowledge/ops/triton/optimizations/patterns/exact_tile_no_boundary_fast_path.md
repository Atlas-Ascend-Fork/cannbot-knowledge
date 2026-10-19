---
type: Optimization
title: Exact-Tile No-Boundary Fast Path
description: 当派发期 shape 守卫能证明无尾 tile 时，把精确 tile 热路径从通用 masked kernel 中拆出，消除边界 mask 与控制分支。
tags: [task.optimization, topic.implementation.masking, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/exact-tile-no-boundary-fast-path.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Exact-Tile No-Boundary Fast Path

## Summary

Split exact-tile hot paths from generic masked kernels when dispatch-time shape guards can prove there are no tail tiles, so Ascend lowering can avoid boundary-only masks, padding values, block-pointer `boundary_check`, and related control branches.

## Use When

The kernel's dominant shapes are exactly divisible by the tile sizes — Python
dispatch can prove it before launch with a cheap guard such as
`M % BLOCK_M == 0 and N % BLOCK_N == 0` — yet the generated code or profiling
still shows boundary checks, masks, or padding on that exact-tile hot path.
A typical example — a mask that guards only block edges:

```python
offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
mask = offs_m < M            # boundary-only: always true when M % BLOCK_M == 0
x = tl.load(ptr + offs_m, mask=mask, other=0.0)
```

The same idea — do boundary work only where a boundary can actually exist —
applies to three related situations:

- **Dispatch-proven case**: the host can prove before launch that this call
  needs no boundary handling (e.g. a short attention call whose sequence fits
  one tile), so dispatch picks a specialized mask-free kernel while the
  generic one stays as fallback.
- **Pre-padded input**: an upstream stage already padded the input to a
  tile-aligned physical length (the logical length is kept separately), so
  loads need no boundary mask at all.
- **Tail-only loop**: only the final iteration of a contraction or recurrence
  loop can be partial, but a generic loop rebuilds the tail mask on every
  iteration — run the full iterations mask-free and peel out the tail.

## Avoid When

- The mask is algorithm semantics, not a boundary/tail guard.
- Exact-divisibility cannot be proven at dispatch.
- Tail-heavy or irregular shapes dominate the workload.
- The main bottleneck is clearly random global memory, atomics, or compute throughput and boundary control is negligible.
- The fast path would duplicate too much complex logic and drift from the fallback.

## Signals

### Code

- `tl.load(..., mask=tail_mask, other=...)` where the mask only protects block edges.
- `tl.store(..., mask=tail_mask)` on shapes known to be full-tile.
- `tl.make_block_ptr` loads or stores keep `boundary_check` for exact shapes.
- Removing the mask does not change address math for the guarded shape.
- A reduction loop computes `k_mask` and clamped K indices in every iteration even though only the final iteration can be partial.

### Profile

- The generic masked kernel is close to the target but still shows scalar/control overhead on the exact-tile path.

## Method

Confirm the fit first: the hot shape must be provably tile-divisible at
dispatch, and every predicate targeted for removal must be classified as a
boundary predicate rather than an algorithmic semantic predicate, because
divisibility can only discharge the first class.

The optimization core is to split a minimal aligned kernel from the generic
masked kernel: remove only the proven boundary masks, padding values, and
block-pointer `boundary_check` on the exact-tile path, and keep the generic
kernel as fallback for every other shape, semantic regime, target, or tile.

### Rule: Dispatch-guard an aligned kernel beside the masked fallback

Add a host-side divisibility guard and route exact shapes to a kernel with no
boundary machinery:

```python
if M % BLOCK_M == 0 and N % BLOCK_N == 0:
    _kernel_aligned[grid](...)
else:
    _kernel_masked[grid](...)
```

Inside the aligned kernel, addressing is pure affine with no masks or padding
values:

```python
offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
value = tl.load(src + offs_m[:, None] * stride_m + offs_n[None, :])
tl.store(dst + offs_m[:, None] * out_m + offs_n[None, :], value)
```

Add host dispatch for a semantic regime only when metadata proves the regime,
and keep causal, prefix, target, window, or ragged predicates still required
inside it. Check each target/compiler and tile independently, because one
exact tile can compile differently from another.

### Rule: Peel the tail chunk out of a full-chunk recurrence loop

For chunked recurrence kernels, the whole sequence may not be tile-divisible,
but every chunk before the last one is still full. Split the recurrence into
a full-chunk hot loop plus one tail block:

- hot loop: `for i_t in range(NT - 1)` with no per-iteration `min`, tail mask, or boundary-only `tl.where`
- tail block: `i_t = NT - 1`, compute `last_idx = min(NT * BT, T) - 1`, and keep the masks needed for the partial final chunk

```python
# Full chunks: no scalar min/mask/where in the hot loop.
for i_t in range(NT - 1):
    last_idx = (i_t + 1) * BT - 1
    b_g_last = tl.load(g_base + last_idx)
    b_g = tl.load(p_g_full_chunk, boundary_check=(0,))
    b_v = b_v * exp(b_g_last - b_g)[:, None]

# Tail chunk: may be partial.
i_t = NT - 1
last_idx = min(NT * BT, T) - 1
m_t = (i_t * BT + tl.arange(0, BT)) < T
b_g_last = tl.load(g_base + last_idx)
b_g = tl.load(p_g_tail, boundary_check=(0,))
b_v = b_v * tl.where(m_t, exp(b_g_last - b_g), 0)[:, None]
```

Use this when only the final chunk can be partial. Avoid it if many chunks are irregular, or if the mask is algorithm semantics rather than boundary protection.

### Rule: Peel the tail dot out of the reduction axis

For a tiled contraction whose reduction length is not divisible, keep every
complete reduction tile on one mask-free hot loop and emit one separately
sized tail dot. This differs from an overlap load: contraction sums are not
idempotent, so the tail must cover each logical reduction element exactly
once.

```diff
- for k0 in range(0, ceil_div(K, BLOCK_K)):
-     k = k0 * BLOCK_K + arange(0, BLOCK_K)
-     valid_k = k < K
-     a = load(A + ..., mask=valid_k)
-     b = load(B + ..., mask=valid_k)
-     acc = dot(a, b, acc)
+ for k0 in range(0, K // BLOCK_K):
+     k = k0 * BLOCK_K + arange(0, BLOCK_K)
+     a = load(A + ...)                 # no K clamp or mask
+     b = load(B + ...)
+     acc = dot(a, b, acc)
+
+if K % BLOCK_K:
+    tail_width = supported_tile_width(K % BLOCK_K)
+    k = (K // BLOCK_K) * BLOCK_K + arange(0, tail_width)
+    # Mask only padding inside this one tail tile when tail_width exceeds
+    # the exact remainder; never revisit a full-loop element.
+    acc = dot(load_tail_a(k), load_tail_b(k), acc)
```

Use a compile-time tail class or a separately specialized kernel so the main
loop no longer carries the boundary machinery. Select a tail width the target
supports; an exact non-power-of-two remainder is not automatically supported,
while padding the tail to the next supported dot width may still be cheaper
than masking every full iteration. Preserve the accumulation order within
each output and validate numerical tolerance, because changing reduction
grouping or dot widths can change floating-point association.

This variant pays off when the masked K path lowers every iteration through clamp, compare, indirect/gather load, or conversion machinery. It is usually unattractive when `K < BLOCK_K`, the main loop has only one iteration, the tail specialization forces a much smaller primary tile, or the compiler already proves all non-final iterations exact.

### Rule: Specialize an exact-width contiguous feature length as constexpr

A per-element address clamp on the *contiguous* (feature) axis — for example
`min(offs_d, D - 1)` protecting a padded tile width — is an identity whenever
the runtime dim equals the tile width, but the compiler cannot prove it.
While it stays in the address expression, every load and store along that
axis loses provable affine-ness and lowers through conservative address
machinery; this can dominate the vector-pipe work feeding Cube dots. Inspect
the instruction timeline and generated address path before keeping this
specialization.

Promote the runtime dim to a `tl.constexpr` kernel argument and specialize:

```python
D_EXACT: tl.constexpr = D == BLOCK_D
if D_EXACT:
    # pure affine addresses, 1-D row masks only
    x = tl.load(ptrs, mask=rows_valid, other=0.0)
else:
    d = tl.minimum(offs_d, D - 1)          # required: unclamped reads go out of bounds
    x = tl.load(ptrs, mask=rows_valid & (offs_d[None, :] < D), other=0.0)
```

Rules to verify on the target:

- Outputs must be bit-identical between the two branches. Keep the exact-width branch only when the generated address path and end-to-end timing show that the removed boundary work matters.
- The clamp is required whenever `D < BLOCK_D`: an unguarded unclamped form reads out of bounds and fails to compile, so do not remove it globally.
- Keep the positional argument binding stable when promoting the dim to `constexpr` (append it as a trailing keyword argument).
- Per-branch loads must preserve each kernel's post-load conversions (a dropped upcast in one branch surfaces as a dot operand-dtype compile error in differential validation).

Build one specialization at a time, compare the specialized kernel against the generic kernel on the exact case, and verify fallback coverage before keeping the split.

## Evidence

Splitting an aligned kernel out of a masked kernel removes boundary-check control overhead on the exact-tile path. The gain is modest when the dominant cost lies elsewhere, such as random global-memory access. Treat this pattern as control-overhead cleanup, not as an access-pattern fix.

## What To Verify After Applying

- Fast path and fallback produce identical values on representative exact-tile shapes.
- Fallback still handles non-divisible shapes.
- The aligned kernel IR no longer contains the targeted boundary checks or masks.
- The specialized kernel beats the generic kernel on the targeted case without broad regressions.
- Every removed predicate is documented as boundary-only; semantic masks remain or are discharged by a host proof.
- Record target/compiler identity and confirm each specialized tile and semantic regime compiles and runs on the device.
- For chunk recurrence tail peeling, test `T < BT`, `T == BT`, `T % BT == 0`, `T % BT != 0`, and varlen branches if present.
- For contraction reduction-axis peeling, confirm the full-loop IR has no K-side clamp/mask/gather, the tail covers the remainder once, and test zero tail, exact supported tail, padded supported tail, and `K < BLOCK_K` fallback cases.

## Related Patterns

- [mask-only-affine-addressing](./mask_only_affine_addressing.md): Try this first when the masked path also carries per-lane clamps. Deleting the clamp while keeping the mask is bit-exact and needs no divisibility proof, dispatch guard, or fallback kernel, so it is strictly cheaper than splitting an exact-tile kernel.
- [compile-hint-adding](./compile_hint_adding.md): Use compiler hints when the structure is sound but lowering misses proven layout or alignment facts.
- [pad-copy-row-col-tiling](./pad_copy_row_col_tiling.md): Rewrite flat 1D copy kernels over `numel(out)` into row–column tiled form to reduce scalar overhead from per-element coordinate reconstruction on the last dimension.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): Use `tl.make_block_ptr` as a compiler-facing representation candidate when source semantics define a regular multidimensional tile but IR suggests that manual pointer expressions lower into unexpectedly scalarized, fragmented, strided, or transpose-heavy memory operations.
- [discrete-access-ub-staging](./discrete_access_ub_staging.md): Stage a contiguous range into the Unified Buffer first, then use on-chip indexing (`tl.gather` or equivalent) to select target values, rather than loading directly from global memory through discrete indices.
- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md): Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md): Introduce and cost a neutral-padded internal representation before this card removes boundary-only predicates from exact consumers.
- [现有知识：Grid 形状与多路径特化](../operator_optimization/grid_dispatch_specialization.md)
- [现有知识：消除冗余边界运算](../operator_optimization/redundant_boundary_operation.md)
