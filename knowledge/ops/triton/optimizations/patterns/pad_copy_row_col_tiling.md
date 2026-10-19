---
type: Optimization
title: Row–Column Tiling for Pad-Copy Kernels
description: 把按 numel(out) 展平的 1D pad-copy kernel 改写为行列分块形式，减少逐元素坐标重建的标量开销。
tags: [task.optimization, topic.tiling, topic.data_movement.data_copy]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/pad-copy-row-col-tiling.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Row–Column Tiling for Pad-Copy Kernels

## Summary

Rewrite flat 1D copy kernels over `numel(out)` into row–column tiled form to reduce scalar overhead from per-element coordinate reconstruction on the last dimension.

## Use When

The kernel is a constant-pad, slice-then-pad, or similar elementwise copy.
It indexes the output as one flat range over `numel(out)` and rebuilds every
coordinate with div/mod arithmetic on each iteration. A typical example:

```python
offsets = pid * BLOCK + tl.arange(0, BLOCK)
d_last = offsets % out_dim_last          # repeated // and % recover coordinates
rows = offsets // out_dim_last
valid = (d_last >= pad_left) & (d_last < pad_left + in_dim_last) & (rows < out_rows)
```

Profiling shows scalar or masked-load/compare cost out of proportion to copy
bandwidth, concentrated at the last-dimension pad boundaries.

The rewrite tiles the kernel as rows × columns: div/mod runs once per row
lane instead of once per element, and the merged `valid` mask splits into
`row_mask & col_mask`.

## Signals

### Code

- Single linear `offsets` and repeated `//` / `%` on **large strides** to recover the **last** coordinate.
- One **global `valid`** merging every dimension on each lane of a large flat block.
- **Multi-phase** column loops (left / interior / right) with **different** `tl.store` masks.

## Avoid When

- The hot path is **gather/scatter** or **index-driven** discrete access (prefer `discrete-access-ub-staging`).
- **Dynamic `if`/`elif` on tile kind** inside the column loop is required without proof the backend lowers it safely—prefer a **uniform** column loop on Ascend unless validated.
- **Interior-only** fast paths that **omit `col_mask`** on `tl.store` without proof for **tail** blocks (`out_dim_last % BLOCK_COLS != 0`).

## Method

Confirm the fit first: the baseline really indexes the output as one flat
range with div/mod coordinate reconstruction, and profiling shows scalar or
mask cost rather than copy bandwidth as the limiter.

The optimization core is to rewrite the kernel into row–column tiled form: a
grid over row blocks, a uniform column loop over the last dimension, and
masks decomposed into `row_mask & col_mask`. Apply the structural rewrite
first, then tune tile sizes one knob at a time; do not combine the rewrite
with unrelated fusion or masking changes.

### Rule: Decompose flat offsets into row lanes plus a uniform column loop

Let `out_rows` be the product of all output dims except the last (after any
fixed-rank padding your stack uses) and `out_dim_last` the last-dim length.
Grid `ceil_div(out_rows, BLOCK_ROWS)` with hardware caps if needed; use a
`tl.range` row stride of `num_programs * BLOCK_ROWS` and
`static_range(BLOCK_ROWS)`; loop columns with
`ceil_div(out_dim_last, BLOCK_COLS)`. Compute the input row base once per row
lane before the column loop, and store with
`store_edge = row_mask & col_mask` where `col_mask = cols < out_dim_last`:

```python
rows = pid * BLOCK_ROWS + tl.arange(0, BLOCK_ROWS)
row_mask = rows < out_rows
in_row_base = ...  # div/mod on row lanes only, computed once
for col_start in range(0, out_dim_last, BLOCK_COLS):
    cols = col_start + tl.arange(0, BLOCK_COLS)
    col_mask = cols < out_dim_last
    # load with row_mask & pad-range mask, store with row_mask & col_mask
```

The div/mod reconstruction now happens once per row lane instead of once per
element.

### Rule: Size `BLOCK_ROWS` by shape

Use **4 or 8** when `out_dim_last` is small and `out_rows` is large; tune
within UB and register limits.

### Rule: Keep `col_mask` on every store

Prefer **one** uniform column loop with `col_mask = cols < out_dim_last` on
every `tl.store`. Do not add an interior-only fast path that omits `col_mask`
unless tail blocks (`out_dim_last % BLOCK_COLS != 0`) are proven safe. Recover
performance through host `BLOCK_COLS` tuning, not through tail-unsafe store
masks.

### Rule: Drop last-dim pad compares when there is no pad (`NO_COL_PAD`)

When `pad_left_last == 0` and `in_dim_last == out_dim_last`, a constexpr
branch removes the last-dim pad compares and sets `in_cols = cols` directly.

### Rule: Tune `BLOCK_COLS` on the host

Optionally skip refinement for a wide-last-dim regime. Otherwise require
**interior column work × rows** to reach a threshold, or halve `BLOCK_COLS`
(floor ~16) with a cap on extra iterations (e.g. avoid **>4×** column
blocks).

### Rule: Choose the masked-load fill strategy by profiling (`NATIVE_MASKED_LOAD`)

The typical versus wide-last-dim load paths are backend- and dtype-dependent.
One useful split is a narrow regime with `other=fill_value` versus a wide
regime with `other=0.0` + fp32 + `tl.where`. Profile both; do not assume the
wide regime always uses `fill_value`.

## What To Verify After Applying

- **Correctness:** **`out_dim_last % BLOCK_COLS != 0`**, asymmetric pad, supported ranks and dtypes.
- **Benchmark:** vs your baseline and framework reference under the same harness.
- **Profiler:** scalar / mask / load mix before changing refinement thresholds.
- **Edge:** zero output numel early exit if applicable.

## Related Patterns

- [logical-layout-tiling](./logical_layout_tiling.md): the generic version of the same flat-index + div/mod → structured-tiling restructure; this card adds the pad/copy-specific disciplines (uniform column loop, `col_mask` on every store, `BLOCK_COLS` tuning).
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): the same row-blocking technique applied to row-reduction kernels (LSE, norms, softmax statistics).
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): Amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.
- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md): Apply **Loop-Invariant Code Motion (LICM)** to Triton kernels: move computations that do **not** depend on the loop induction variable out of the loop, so each iteration performs only the minimal work that truly varies.
- [autotune](../operator_optimization/autotune.md): Use Triton-Ascend autotune as the default way to search split sizes, tile sizes, and selected compile options when the kernel structure is already reasonable and the main open question is parameter choice.
- [compile-hint-adding](./compile_hint_adding.md): Use compiler hints when the structure is sound but lowering misses proven layout or alignment facts.
- [vec-cmp](./vec_cmp.md): Rewrite explicit integer compare-heavy logic into a form that is more vector-friendly on Ascend NPU, especially when scalarized compares are blocking fast masking or selection.
- [现有知识：维度合并优化](../operator_optimization/dimension_merge.md)
