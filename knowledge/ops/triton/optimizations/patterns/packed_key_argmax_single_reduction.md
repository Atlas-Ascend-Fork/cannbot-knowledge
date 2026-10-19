---
type: Optimization
title: Packed-Key Single Reduction for Extremum-with-Index
description: 把带首次出现位置的极值归约打包为单次 key 归约，或以 pair32/pair64 双归约规避慢的宽整数比较路径。
tags: [task.optimization, topic.compute.reduction, topic.compute.ordering]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/packed-key-argmax-single-reduction.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Packed-Key Single Reduction for Extremum-with-Index

## Summary

Any reduction that must emit an **extremum together with the position of its first occurrence** (argmax/argmin, top-k extraction rounds, cummin/cummax-style scans, pooling-with-indices) normally costs two reductions per extraction — one for the value, one for the index — or a slow tuple reduce. Instead, encode value and position into a **single order-preserving integer key** so that one `tl.max` yields both: the monotonic value bits occupy the high field, the inverted position occupies the low field, so key order equals value order and ties resolve to the smallest index for free, matching torch semantics.

## Use When

The kernel reduces a whole tile and must return both an extremum value and the
position of its first occurrence — argmax/argmin, top-k extraction rounds, or
pooling-with-indices. The current implementation pays two reductions per
extraction: one for the value and one for the index.

```python
best_val = tl.max(work, axis=1)
best_idx = tl.argmax(work, axis=1)   # second full reduction over the same tile
```

The argmax/top-k extraction reduces a whole tile at once — or one round per
top-k step. Ties must resolve to the first occurrence, matching
`torch.argmax` / `torch.topk` semantics.

Packing value and position into one integer key fuses the value and index
reductions into a single `tl.max`, removing a full pass over the tile.

## Avoid When

- **Per-element serial scans**: building a packed key per scalar element inside a sequential `for k in range(red_size)` loop can cost more than the native `compare + two selects` chain. The pattern is intended for tile-level reduction; restructure to tile loads first, then apply the key.
- The required ordering is not (value, then smaller position) — e.g. stable sort or lexicographic multi-key.
- The position range exceeds the low field (use chunk-local positions plus a merge pass instead of widening the key blindly).
- A wide-key reduction is measured slower than the pair form on the target (on Ascend 950, int64 vector ALU is slow enough that pair32 usually wins for fp32/int32 inputs).

## Signals

### Code

- `best_val = tl.max(work, axis)` followed by `best_idx = tl.argmax(work, axis)` or an equivalent where+min index search.
- A k-round extraction loop re-running both reductions and masking out each winner with `work = tl.where(found, extreme, work)`.
- fp16/bf16 inputs being upcast to fp32 only so the comparison math is easier — the key can be built on native 16-bit values directly.

### IR / Profile

- Two `tt.reduce` operations per extraction round.
- Wide integer ALU (`extsi`/`xori`/`shli` on i64, or i16 bitcast chains) in the compare path — prefer 32-bit key fields on Ascend 950.
- fp16 reduces lowered as full-tile `arith.extf` → fp32 reduce → `arith.truncf`.

## Method

Confirm the fit first: the kernel reduces a tile in one operation and the
value and index reductions both walk the same tile, so fusing them into one
keyed reduction removes a full tile pass. If the reduction is a per-element
serial loop, restructure to tile loads before applying anything here.

The optimization core is to pack the value's monotonic bit-mapping into the
high field of one integer key and the inverted position into the low field,
then extract both with a single `tl.max`. Apply the rules below in order.

### Rule: Map value bits to monotonic unsigned order

For the two's-complement bit pattern `b` of the value, flip so unsigned order
equals value order:

```python
u = b >= 0x8000 ? b ^ 0xFFFF : b ^ 0x8000   # fp16; fp32: 0x80000000 / 0xFFFFFFFF
```

**Zero-extend 16-bit patterns into int32** (`bitcast_i16 → int32 & 0xFFFF`); a
sign-extended int16 breaks the mapping.

### Rule: Pack value high, inverted position low

```python
key = ((u ^ SIGN) << POS_BITS) | (POS_MASK - pos)
```

The extra `^ SIGN` flip is mandatory — without it, positive values produce
negative signed keys and sort **below** negative values. Inverting the
position makes ties resolve to the smallest index, matching torch semantics.

### Rule: Extract once, decode exactly

```python
best = tl.max(key, axis=1)
pos  = POS_MASK - (best & POS_MASK)
```

If values are emitted, invert the mono map (`u >= SIGN ? u ^ SIGN : u ^
FULL`). An inverted branch condition here yields correct indices but garbage
values — an easy bug to make.

### Rule: Eliminate winners by key in top-k loops

```python
key = tl.where(key == best_key, MIN_KEY, key)
```

This masking is exact because keys are unique per position, so no separate
position bookkeeping is needed between rounds.

### Rule: Let NaN order itself through the key

NaN needs no substitution: quiet-NaN patterns map above +inf, so NaN wins
`largest` extraction with first-index tie-break and sinks after mono inversion
for `smallest`. Detect a NaN pick by the constant key-high field (fp16
`0x7E00`, bf16 `0x7FC0`, fp32 `0x7FC00000`) and emit `nan` for it — no
reloads, no second value pass.

### Rule: Match key width to dtype

- fp16/bf16 → 32-bit key.
- fp32/int32 → measure the pair32 form (`tl.max` + `tl.min(tl.where(v == mv, pos, N))`) against the 64-bit key; on Ascend 950 pair32 usually wins because the bottleneck is wide-integer ALU, not the second reduction.
- int64 → pair64 (wide-key reduce loses to pair on Ascend 950).

### Rule: Dispatch the tiling by case class

One key/pair kernel cannot be optimal for every shape; dispatch on (dtype ×
reduction position × length × output parallelism):

- dim = last (contiguous rows): rows tile `[BLOCK_M, BLOCK_N]` + `tl.max(axis=1)`; use a two-stage split (partial keys + merge) when `red_size` is huge and output count is tiny (e.g. 1-D), and exact or single-iteration tiles when `red_size <= BLOCK_N`.
- dim ≠ last (strided): `[K_TILE, BLOCK_I]` tiles over `[outer, red, inner]` + `tl.max(axis=0)`; split along `red` (part + merge) when `outer * inner_blocks` underfills the grid.

### Discipline

Change one thing at a time and measure the packed-key or pair form against the
original value/index reduction on representative and boundary shapes. Keep
per-element serial scans separate: the key encoding exists to reduce a tile
in one operation, not to add packing work inside a sequential scalar loop.

## Backend Pitfalls To Check On The Target

- `v.to(tl.int32, bitcast=True)` of `-inf` may lower to a saturating convert returning `0x80000000` instead of `0xFF800000`; patch in the value domain (`b = tl.where(v == -inf, 0xFF800000, b)`, fp16 `0xFC00`, bf16 `0xFF80`) when the value must round-trip.
- `tl.argmax` on `[M, N]` tiles, tuple reductions, or same-address atomics may lower worse than the manual pair reduction and may use maxnumf semantics that drop NaN. Inspect the generated path and compare packed-key or pair forms before choosing one.

## What To Verify After Applying

- Duplicated extrema return the first index (quantized dtypes produce heavy ties).
- NaN rows, ±inf rows, -0.0 vs +0.0, all-equal rows, `smallest=True/False` variants.
- Index and value outputs both bit-exact when values are emitted (decode round-trip).
- Position-range and bit-width behavior on boundary shapes before promotion.

## Related Patterns

- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md) — wide-integer ALU avoidance that motivates 32-bit keys.
- [overlap-tail-load-mask-free](./overlap_tail_load_mask_free.md) — relies on the same position-aware tie-breaking to tolerate duplicate lanes.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md) — mask elimination for the tiles feeding the reduction.
- [现有知识：Histogram-like / Small-Output-Table Reduction](../operator_optimization/histogram_like_table_reduction.md)
