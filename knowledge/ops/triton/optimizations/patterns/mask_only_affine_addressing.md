---
type: Optimization
title: Mask-Only Affine Addressing
description: 删除已带边界 mask 的访存指针表达式中的逐 lane 索引 clamp，保留原始仿射偏移，让谓词承担越界保护。
tags: [task.optimization, topic.implementation.masking, topic.data_movement.memory_access]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/mask-only-affine-addressing.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Mask-Only Affine Addressing

## Summary

Delete per-lane index clamps from pointer expressions whose load or store already carries a boundary mask, keeping raw affine offsets in the address and letting the predicate do the protecting. A clamp such as `tl.minimum(offs, N - 1)` makes the address data-dependent, so the compiler can no longer prove the tile is a contiguous slice and lowers it to an indirect/gather load whose cost scales with lane count instead of bytes moved. The rewrite is bit-exact and unconditional: valid lanes keep identical addresses, and `mask=0` lanes are never dereferenced.

## Use When

A load or store clamps regular offsets with `tl.minimum` / `tl.maximum`
against a dimension bound (`M - 1`, `N - 1`, `K - 1`), even though the same
`tl.load` or `tl.store` already carries a boundary mask — the clamp protects
nothing the mask does not. A typical example:

```python
offs_c = tl.minimum(offs, N - 1)             # clamped index
tile = tl.load(ptr + offs_c, mask=offs < N)  # mask already guards it
```

The clamp is often recomputed inside a reduction loop on every iteration even
though only the last iteration can be partial.

## Avoid When

- The clamp implements wraparound, replication, edge extension, or another real index mapping. That is algorithm semantics, not boundary protection, and removing it changes results.
- The load or store has no mask and none can be added, so raw offsets would dereference out-of-range addresses.
- The indices are genuinely data-dependent (`x[idx]` with runtime `idx`). The addresses cannot be made affine and no clamp removal helps; see `discrete-access-ub-staging`.
- A local band can start at a negative logical coordinate. Clamp a scalar tile origin once per program instead and keep the exact semantic predicate for lanes near the band edge.
- A consumer is intentionally mask-free. Use an initialized tile-aligned internal layout rather than reading invalid raw addresses; see `amortized-neutral-padding-layout`.

## Signals

### Code

- `tl.minimum(offs_m, M - 1)` or equivalent appears in the same expression that already computes `offs_m < M` for the mask.
- Separate `*_clamped` and `*_mask` values are derived from the same offset vector and used together in one load.

### Profile

- Per-lane address work lands on the **vector** engine, not the scalar one, so a high `aiv_vec_ratio` coexists with an idle cube and idle MTE. Do not require a high scalar ratio before considering this card.
- Kernel time scales with tile area rather than with valid lanes or bytes moved.
- A moved-bytes / bandwidth lower bound sits far below measured kernel time.

### IR

- The affine tile operand is lowered as an indirect, gather-style load or store (e.g. `triton_indirect_load` / `triton_indirect_store`).

## Method

Confirm the fit first: the load or store already carries a mask that covers
exactly the lanes the clamp folds in, and IR shows the affine operand lowered
as an indirect, gather-style access (e.g. `triton_indirect_load` /
`triton_indirect_store`).

The optimization core is to keep raw affine offsets in the pointer expression
and let the mask do all the boundary protection.

### Rule: Delete the clamp, keep the raw affine offset

```python
# Before: lane-wise clamps turn a regular tile into indirect addresses.
rows_safe = tl.minimum(rows, M - 1)
cols_safe = tl.minimum(cols, N - 1)
tile = tl.load(base + rows_safe[:, None] * stride_m + cols_safe[None, :],
               mask=(rows[:, None] < M) & (cols[None, :] < N), other=0.0)

# After: valid lanes retain the same addresses; the mask protects the rest.
valid = (rows[:, None] < M) & (cols[None, :] < N)
tile = tl.load(base + rows[:, None] * stride_m + cols[None, :],
               mask=valid, other=0.0)
```

The rewrite is bit-exact: valid lanes keep identical addresses, and masked
lanes are never dereferenced.

Apply the rule kernel by kernel in hot-cost order rather than across the
repository in one edit, so each removal can be measured against the previous
kernel version on its own. Prefer this card over
`exact-tile-no-boundary-fast-path` when both apply: that card removes the mask
itself and must prove divisibility, add a dispatch guard, and keep a fallback
kernel, while this one keeps the mask, needs no guard, and works for every
shape.

## What To Verify After Applying

- Correctness before performance: the rewrite should be bit-exact, so a nonzero max-abs difference means a clamp carried semantics and must be restored.
- Every removed clamp had a mask on the same load or store covering exactly the lanes the clamp used to fold in.
- IR for the edited kernel no longer lowers those operands as indirect, gather-style accesses (e.g. no `triton_indirect_load` / `triton_indirect_store` remains).
- Boundary shapes where the tail tile is partial, and shapes where the length is exactly tile-divisible.
- Before-and-after benchmark on the edited kernel, not just the operator geomean, so the attribution stays with one kernel per round.

## Related Patterns

- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md): the broader lowering-cleanup checklist this card was split out of; consult it for constexpr parameters, loop-carried pointer recurrences, modulo addressing, single-position `tl.where`, int32 vector arithmetic, and cumsum axis handling.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md): removes the boundary predicate itself once divisibility is proven at dispatch; heavier than this card and conditional on shape.
- [overlap-tail-load-mask-free](./overlap_tail_load_mask_free.md): covers a non-divisible length with two unmasked loads for idempotent reductions, and warns against reintroducing clamped indices in their place.
- [discrete-access-ub-staging](./discrete_access_ub_staging.md): for genuinely data-dependent gathers, where the addresses cannot be made affine and staging is the correct answer.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): an alternative compiler-facing representation when manual pointer expressions still lower into scalarized or fragmented memory operations.
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md): introduce an initialized physical layout when repeated consumers need mask-free raw affine loads.
- [ragged-tile-early-return](./ragged_tile_early_return.md): remove whole programs whose tiles lie outside a segment-local length, instead of repairing addressing for a program that still has live lanes.
- [现有知识：消除冗余边界运算](../operator_optimization/redundant_boundary_operation.md)
