---
type: Optimization
title: 循环不变量外提
description: 外提循环内不变的计算与加载，同时检查存活范围、资源压力和搬运开销。
tags:
- task.optimization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/loop-invariant-hoisting.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Loop-Invariant Hoisting Pattern

## Summary

Apply loop-invariant code motion to source loops and compiler-generated element
loops: compute fixed addresses, masks, or reduced block factors and load stable
input tiles once at their natural length, then reuse them across iterations or
broadcast them over the element tile. Confirm that lowering keeps expensive
invariant work outside the loop.

## Use When

A hot tiled loop rebuilds addresses, masks, or window bounds, or reloads stable
input tiles, without dependence on its induction variable. Profiling or IR shows
that this repeated transfer, scalar, or control work is a large share of the
loop's cost.

A second case is a reduction that produces only a few values per row or block.
A following step computes a scale or a reciprocal from those values, or converts
them to another dtype, and broadcasts the result over a much larger element
tile. The lowered code recomputes that small step inside the element loop even
though its inputs do not change there.

## Signals

### Code

- Inner loop recomputes expressions of the form:
  - `base(pid, offs) + delta(loop_var)`
  - e.g. `a_ptr + offs_m*stride_am + k*stride_ak`
- Masks are rebuilt each iteration even when parts are invariant:
  - e.g. `a_mask_m = offs_m < M` is invariant, but recomputed into `a_mask` each iter.
- A loop reloads the same tile with invariant addresses and masks, and no
  intervening write changes its data.

### IR

- Repeated arithmetic chains (`muli/addi/index_cast`) inside `scf.while` / `scf.for` bodies.
- Loop bodies contain repeated `subi/minsi/maxsi` patterns for bounds handling.
- A compiler-generated element-conversion loop contains repeated division or
  casts of the same reduced statistic.

### Profile

- AIV scalar dominated by `LD_XD_XN_IMM`, `ST_XD_XN_IMM`, `ADD(_IMM)`, `CMP_IMM`.
- Timeline shows CUBE waiting on flags around the loop, while AIV performs control-heavy work.
- A reduction-to-conversion region costs disproportionately in the Vector pipe
  relative to its number of independent factors.

## Method

Confirm the fit first: source or lowered loop bodies must repeat work whose
inputs are invariant for that loop. IR or profiling must attribute a large share
of the loop's cost to that repetition, whether scalar address work or compact
vector math.

Split address expressions into an invariant base and a varying delta, or
evaluate reduced-state arithmetic at its compact length before broadcasting
over the element tile. Apply one lever at a time from the list below.

### Lever: Hoist invariant pointer bases

Move the loop-invariant part of tile addresses out of the loop:

```diff
- k = 0
- while k < K:
-     k_offs = k + offs_k
-     a_ptrs = a_ptr + (offs_m[:, None] * stride_am + k_offs[None, :] * stride_ak)
-     b_ptrs = b_ptr + (k_offs[:, None] * stride_bk + offs_n[None, :] * stride_bn)
+ a_base = a_ptr + offs_m[:, None] * stride_am
+ b_base = b_ptr + offs_n[None, :] * stride_bn
+ k = 0
+ while k < K:
+     k_offs = k + offs_k
+     a_ptrs = a_base + k_offs[None, :] * stride_ak
+     b_ptrs = b_base + k_offs[:, None] * stride_bk
```

Keep address arithmetic at its natural length before broadcasting. For an
indexed row gather, compute `source_offset = source.to(tl.int64) * WIDTH` as a
one-dimensional vector and only then add `source_offset[:, None, None]` to the
element tile. Do not widen a provably in-range dense output-row offset to
`int64` merely because the indirect input offset needs it. Inspect TTIR/IR for
an extend/multiply on the compact row vector rather than after 3-D expansion;
the two source expressions are mathematically equal but need not lower to the
same scalar/vector work.

### Lever: Hoist invariant mask and bound parts

Precompute mask components that do not vary with the loop and combine them with the per-iteration part:

```python
a_mask_m = offs_m < M    # invariant
b_mask_n = offs_n < N    # invariant
while k < K:
    k_offs = k + offs_k
    a_mask = a_mask_m[:, None] & (k_offs[None, :] < K)
    b_mask = (k_offs[:, None] < K) & b_mask_n[None, :]
```

### Related mechanism: Closed-form window divisors

Replacing per-tap counting with a formula eliminates a recurrence rather than
hoisting invariant work. [`simt-window-divisor-formula`](simt_window_divisor_formula.md) owns that construction
and its padding semantics; this card owns reuse of its fixed bases and bounds.

### Lever: Hoist attention query and rope tiles

In attention kernels the query tile (and the query-rope tile) can be invariant
with respect to both the KV loop and the inner D-chunk loop while being
reloaded inside them. Load the stable tiles and their masks once per program,
then index the cached tiles inside the loops. Prove that the pre-loop loads are
valid even when the loop has no iterations, that no intervening write changes
the data, and that keeping the tiles live fits UB. Retain the original load
dtypes and recheck allocation when combining hoisting with tiling or precision
changes.

### Lever: Compute compact factors before element conversion

Keep a row-by-block reduction at its natural length. Flatten the independent
statistics, compute the scale or nonlinear chain once in an outlined SIMD
region, then reshape the factors and broadcast them over the element tile.
With the staged CANN API, `ascend.scope(vector_mode="simd", outline=True,
no_inline=True)` can keep this factor-production region separate from the
compiler-generated element loop. Verify that separation in generated IR or
device code; the API spelling is not a guarantee of profitable lowering.

```python
import triton.extension.buffer.language as bl
from triton.language.extra.cann import extension as ascend

# stats is (ROWS, BLOCKS); FACTORS = ROWS * BLOCKS is compile-time.
tl.static_assert(FACTORS % VECTOR_LANES == 0)
stats_flat = tl.reshape(stats, (FACTORS,))
storage = bl.alloc(factor_dtype, [FACTORS], ascend.ascend_address_space.UB)
factor_flat = bl.to_tensor(storage)
with ascend.scope(vector_mode="simd", outline=True, no_inline=True):
    for offset in range(0, FACTORS, VECTOR_LANES):
        piece = ascend.extract_slice(stats_flat, [offset], [VECTOR_LANES], [1])
        rounded_factor = (limit / piece).to(factor_dtype)
        factor_flat = ascend.insert_slice(
            factor_flat, rounded_factor, [offset], [VECTOR_LANES], [1])
factor = tl.reshape(factor_flat, (ROWS, BLOCKS))
scaled = (values * factor[:, :, None]).to(values.dtype)
```

Select the slice length from the target SIMD form and supported dtype; the
example assumes an exact number of slices. Allocate UB storage without a
zero-fill only after proving every factor slot is overwritten before its first
read. For a partial final slice, use a supported padded or masked form with
complete valid coverage. Keep the compact buffer and live element tile within
compiler-reported UB capacity.

Preserve the original safe-statistic rule, factor dtype and rounding, element
multiply rounding, and final conversion semantics. When lowering merges an
observable intermediate downcast into the final conversion, emit that downcast
explicitly with the required CANN `ascend.cast` rounding mode before the final
cast. Moving division to a compact region does not permit changing clamps,
saturation, or the arithmetic contract.

Apply that explicit cast only on the shape or semantic branch whose original
contract requires it. Do not globally promote a BF16 element multiply to FP32
merely because a special unguarded-statistic shape needs an explicit
FP32-to-BF16 rounding point. Compare per-shape TTIR: the ordinary branch should
retain its BF16 multiply/direct FP8 conversion when that is the original
contract, while the exceptional branch retains the explicit rounding and
saturation sequence.

Preserve broadcast orientation (`[:, None]` vs `[None, :]`) when splitting
addresses and masks. Hoisting preserves the arithmetic and rounding contract;
layout-transform costs such as ND2NZ belong to separate patterns.

## Avoid When

- An expression depends on the loop variable, or a load observes data changed
  by an intervening write; its value is not invariant.
- Moving a load before the loop would access an invalid address or execute an
  access that the original empty-loop or boundary guard suppressed.
- Retaining the invariant tiles or compact factors exceeds usable UB, adds
  costly transfers, or makes total operator latency worse.
- Lowering still repeats the factor chain inside the element iterations; source
  placement alone does not establish that the mechanism was applied.

## What To Verify After Applying

1. **Correctness**: compare against reference across boundary shapes (non-multiples of block sizes).
2. **Profiler**: reduced scalar instruction mix (`LD/ST/ADD/CMP`) and improved wall time.
3. **IR sanity**: fewer repeated arithmetic ops inside loop bodies (qualitative evidence).
4. **Compact factors**: confirm division and factor rounding occur once per
   independent statistic outside the element iterations, and that generated IR
   shows one factor-production region followed by the element region consuming
   those factors. A source-level placement before a broadcast is not proof of
   hoisting; inspect the lowered operand length. Check that every UB slot is
   defined before use, and that a whole-buffer initialization is absent only
   under full coverage.
5. **Numerics and cost**: cover zero and near-zero statistics, rounding ties,
   saturation boundaries, and partial factor lengths permitted by the contract.
   Compare compact-region cost, UB allocation, repeated vector work, added
   transfer, and complete operator latency.

## Related Patterns

- [`compute-once-share-via-gm`](compute_once_share_via_gm.md): use when an invariant spans consumer programs and cannot remain in registers or UB under legal ownership.
- Complements **[`compile-hint-adding`](compile_hint_adding.md)**: after LICM, add alignment/contiguity hints.
- Complements **[`software-pipeline`](software_pipeline.md)**: LICM simplifies loop bodies; pipeline overlaps remaining transfer/compute.
- Complements **[`implicit-transpose-elimination`](implicit_transpose_elimination.md)**: layout fixes reduce transform work; LICM reduces residual loop control cost.
- [`simt-window-divisor-formula`](simt_window_divisor_formula.md) — algebraic normalizer replacement plus clip-window loads for fixed-window reduces: Use closed-form clipped bounds when full-window masked counting is costly.
- [`algebraic-optimization`](algebraic_optimization.md): Apply mathematical identities and semantics-preserving rewrites to reduce redundant memory passes, full data scans, contraction work, intermediates, or live ranges before micro-tuning loads.
- [`invariant-preprocessing-cache`](invariant_preprocessing_cache.md): Reuse pure preprocessing results across public operator invocations under explicit contracts for cache identity, invalidation, ownership, bounded storage, and cold-versus-warm cost.
- [`large-tile-fit-enabling`](large_tile_fit_enabling.md): When a valuable large tile fails UB planning, inspect the extra temporaries created by calculations on the large tile.
- [`scattered-transfer-batching`](scattered_transfer_batching.md): Batch the contiguous side of indexed movement in UB to reduce small global transfers.
- [`kernel-fusion-and-value-placement`](kernel_fusion_and_value_placement.md): settled grouping and value placement bound where invariant work can stay; hoist within that boundary rather than across it.
