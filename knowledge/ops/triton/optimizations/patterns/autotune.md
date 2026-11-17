---
type: Optimization
title: Autotune 参数搜索决策
description: 结构稳定后优先自动搜索参数，再按推断能力与合法空间选择 hints 或手写配置。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/autotune.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Triton-Ascend Parameter Autotuning

## Summary

Optimize tile geometry, split sizes, buffering options, and the row-batch and
worker split of an established SIMT path through a bounded search over
configurations that compile, after the kernel structure is settled. Preserve
numerical dataflow and derive launch coverage from each candidate so parameter
tuning improves the complete operator.

## Use When

The kernel is correct and its structure is settled (earlier-stage rewrites
applied or ruled out), and the remaining headroom is in parameter choice:
exposed compile-time tile sizes, split shape, buffering, or supported launch
options. For an established SIMT row-reduction path, that headroom can also lie
in row-batch size and SIMT worker count while the feature-side computation and
the reduction body stay fixed. The kernel may expose those choices as
`tl.constexpr` parameters, or keep them fixed behind a persistent launch
geometry that already covers every row.

## Avoid When

- The real problem is structural, such as a manual matmul or reduction that should first become a regular tiled `tl.dot` loop.
- All relevant tile and launch options are fixed, leaving no meaningful tuning space.
- Semantic constraints leave, after pruning, no configurations that compile and still differ in a useful way; a fixed grid axis alone can still permit an explicit search over other choices.
- Coupled parameters have no provable candidate-dependent grid, loop stride, or tail coverage. Incomplete automatic parsing alone calls for hints or explicit candidates.
- The kernel is correctness-fragile under repeated benchmarking and has not yet added the reset or restore hooks needed for safe autotune evaluation.

## What To Verify After Applying

- Verify the chosen route is the least manual one that still fits the kernel:
  - `configs=[]` first when parser inference should succeed
  - `hints` when semantics are clear but inference is incomplete
  - explicit `triton.Config` lists only when the search space truly needs manual control
- Verify `key` tracks the runtime shape arguments that actually change the best configuration.
- Verify update-style kernels use `reset_to_zero`, `restore_value`, hooks, or equivalent safeguards so repeated autotune trials do not corrupt outputs.
- Verify the searched parameters are Ascend-relevant: generally `BLOCK_*`, `multibuffer`, and `unit_flag`; for an established SIMT path, a bounded joint row-batch/`num_warps` search is eligible when target measurements confirm sensitivity. Keep `num_stages` fixed unless it has independent evidence.
- Verify `TRITON_PRINT_AUTOTUNING=1` or equivalent logs show the inferred axes, candidate count, and chosen best configuration during debugging.
- Verify the selected block sizes still satisfy semantic constraints such as `BLOCK_SIZE <= tiled logical extent` when padding would otherwise change results.
- Verify each candidate's meta-dependent grid, persistent tile stride, and tail owner cover every row exactly once, including row counts smaller than one batch and tile counts around the program cap.
- Verify steady-state gains in repeated matched runs, including the intended integrated shape mix when it supplied the bottleneck evidence; retain the same feature-side computation, accumulation order, and epilogue during row-batch and worker-count tuning.

## Route 1: Automatic Autotune First

Use `configs=[]` first when split and tiling structure can be inferred directly from the kernel DSL.

Typical signals:

- the free tuning parameters are `tl.constexpr` values not fixed at launch time
- split parameters come from `tl.program_id`
- tiling parameters come from `tl.arange` or loop step structure
- masks or bounds expressions map cleanly back to runtime shape axes

```python
@triton.autotune(
    configs=[],
    key=["n_rows"],
)
@triton.jit
def kernel(
    x_ptr,
    y_ptr,
    n_rows,
    BLOCK_M: tl.constexpr,
):
    pid = tl.program_id(0)
    offs = pid * BLOCK_M + tl.arange(0, BLOCK_M)
    mask = offs < n_rows
    x = tl.load(x_ptr + offs, mask=mask, other=0)
    tl.store(y_ptr + offs, x, mask=mask)
```

## Route 2: Add `hints` Before Hand-Writing Configs

Use `hints` when the kernel still fits auto-generated search, but parser inference is incomplete.

Typical signals:

- the split or tiling parameter is semantically clear to a human reviewer
- the path from `program_id` or `tl.arange` to masks is indirect
- low-dimensional or reduction axes need to be stated explicitly

When using `hints`, prefer axis-named `key` mappings so the cache aligns with the hinted axes.

```python
@triton.autotune(
    configs=[],
    key={"x": "n_rows", "y": "n_cols"},
    hints={
        "split_params": {"x": "BLOCK_M"},
        "tiling_params": {"y": "BLOCK_N"},
        "low_dim_axes": ["y"],
        "reduction_axes": [],
    },
)
@triton.jit
def kernel(
    x_ptr,
    y_ptr,
    n_rows,
    n_cols,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
):
    pid = tl.program_id(0)
    offs_m = pid * BLOCK_M + tl.arange(0, BLOCK_M)[:, None]

    for n0 in range(0, n_cols, BLOCK_N):
        offs_n = n0 + tl.arange(0, BLOCK_N)[None, :]
        mask = (offs_m < n_rows) & (offs_n < n_cols)
        x = tl.load(x_ptr + offs_m * n_cols + offs_n, mask=mask, other=0)
        tl.store(y_ptr + offs_m * n_cols + offs_n, x, mask=mask)

# This kernel covers columns internally, so the launch stays 1-D:
# grid = (triton.cdiv(n_rows, BLOCK_M),)
```

## Route 3: Hand-Write `triton.Config` Candidates Last

Use explicit `triton.Config` lists only when the search space must be constrained manually.

Typical signals:

- one grid axis is fixed by semantics and cannot be freely split
- one parameter couples launch count and inner tile shape
- the kernel exposes too little clean tuning structure for automatic generation
- candidate quality is still poor after adding `hints`

On Triton-Ascend, the main hand-written search dimensions should usually be:

- `BLOCK_*` sizes
- `multibuffer`
- `unit_flag` when relevant
- `BAND` / window extent when the kernel covers a bounded visible support
  per row block; legality requires `BLOCK_M + visible_band <= BAND`, and
  the smallest covering `BAND` should be preferred over a fixed wide value
  (wider windows multiply resident key/value/probability tiles and can
  cross the unified-buffer budget)
- geometry ladder ordering: enumerate `(BLOCK_M, BAND)` candidates in
  coverage-ascending order and gate each `(dtype, head-dim tile, BAND)`
  combination on a measured win before dispatching to it

Keep general search focused on Ascend tile and buffer options. For an established SIMT path, including arithmetic and reduction kernels, `num_warps` can also be a measured work-split axis.

```python
def get_configs():
    return [
        triton.Config({"BLOCK_M": bm, "BLOCK_N": bn, "multibuffer": mb})
        for bm in [256, 128, 64, 32]
        for bn in [128, 64, 32, 16]
        for mb in [True, False]
    ]

@triton.autotune(
    configs=get_configs(),
    key=["n_rows", "n_cols"],
)
@triton.jit
def kernel(
    x_ptr,
    y_ptr,
    n_rows,
    n_cols,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
):
    pid_m = tl.program_id(0)
    pid_n = tl.program_id(1)
    offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)[:, None]
    offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)[None, :]
    mask = (offs_m < n_rows) & (offs_n < n_cols)
    x = tl.load(x_ptr + offs_m * n_cols + offs_n, mask=mask, other=0)
    tl.store(y_ptr + offs_m * n_cols + offs_n, x, mask=mask)

# The launch must cover both axes:
# grid = (triton.cdiv(n_rows, BLOCK_M), triton.cdiv(n_cols, BLOCK_N))
```

### Bounded SIMT row-batch and worker search

Keep the selected compile mode, feature-side layout, accumulation, and
epilogue fixed. Enumerate configurations that pair row-batch size with
`num_warps` via `triton.Config`, keeping stage count fixed so the comparison
isolates the row-batch and worker choice. Use explicit candidates when a
persistent program cap or tile constraints require a narrower search than
automatic inference supplies. Key the search by the runtime shape arguments
that change the best choice, and compute the launch grid from each candidate's
meta values.

For a persistent row-tile loop, let `T = cdiv(rows, row_batch)` and launch
`min(T, program_cap)` programs, with a cap justified for the target and
launch mode. Bind loop stride and tail ownership to that launched count.
A fixed cap as the stride is also valid when coverage is proved for both
`T < program_cap` and `T >= program_cap`, including the partial final tile.
This keeps the existing row ownership while tuning its granularity;
[`program-multiple-rows`](program_multiple_rows.md) supplies the batching construction when it is absent.

## When Automatic Parsing Usually Fails

Prefer `hints` or custom configs when you see one or more of the following:

- the kernel has no meaningful free `tl.constexpr` parameters because they are fixed at launch or coupled too tightly to semantics
- no clear mask or bounds relation back to the runtime axis
- one parameter must cover an entire semantic dimension, such as `BLOCK_SIZE >= hidden_dim`
- a business or semantic rule fixes one grid dimension instead of allowing free tiling
- one parameter influences multiple axes at once

## Ascend-Specific Notes

- Default config-space search should focus on `BLOCK_*`, `multibuffer`, and `unit_flag`; add bounded `num_warps` candidates for an established SIMT path when target evidence identifies worker partition as a lever.
- When launch hints interact, include a small bounded set of Ascend-relevant options such as `multibuffer`, `set_workspace_multibuffer`, or `enable_auto_bind_sub_block` instead of hand-picking one globally.
- If you are applying [`force-simt-only-discrete-access-950`](force_simt_only_discrete_access_950.md), recheck `num_warps` and grid decomposition there after enabling `force_simt_only=True`.
- For update-style kernels, repeated autotune evaluation can write outputs multiple times. Add `reset_to_zero`, `restore_value`, `pre_hook`, or `post_hook` before trusting benchmarks.
- Start debugging with `TRITON_PRINT_AUTOTUNING=1`.

## Related Patterns

- [`tile-footprint-fitting`](tile_footprint_fitting.md): use it first when the kernel still needs a better tiled structure before any search space should be explored.
- [`software-pipeline`](software_pipeline.md): use it when the tile structure is already good and the next issue is overlap quality rather than parameter choice.
- [`force-simt-only-discrete-access-950`](force_simt_only_discrete_access_950.md): use it when Ascend 950 is confirmed and the kernel is discrete-access-ub-staging dominated; that launch-mode experiment intentionally rechecks `num_warps` and grid decomposition after `force_simt_only=True`.
- [`algebraic-optimization`](algebraic_optimization.md): Apply mathematical identities and semantics-preserving rewrites to reduce redundant memory passes, full data scans, contraction work, intermediates, or live ranges before micro-tuning loads.
- [`arithmetic-intensity-balancing`](arithmetic_intensity_balancing.md): Choose tile sizes and work assignment by comparing estimated per-tile compute cycles against per-tile memory-transfer cycles, so the bottleneck lands on the resource whose consumption has a hard floor (FLOPs for matmul-like kernels, bytes for movement-bound kernels).
- [`dot-operand-precision-ablation`](dot_operand_precision_ablation.md): Ablate matched lower-precision `tl.dot` operands independently from accumulator, recurrence or epilogue, and output precision.
- [`grid-flatten-and-ub-buffering`](grid_flatten_and_ub_buffering.md): Flatten logical work items onto physical cores and batch small row-wise memory transfers into wider UB stores to reduce launch overhead and improve per-core work density.
- [`implicit-transpose-elimination`](implicit_transpose_elimination.md): Eliminate implicit transpose-style access on Ascend NPU by ensuring operands are in the physical layout the kernel needs, avoiding compiler-injected layout transforms.
- [`reduction-axis-split-combine`](reduction_axis_split_combine.md): When a reduction kernel's parallelism is capped by its non-reduction grid (the launch cannot fill the cores), split the REDUCTION axis across programs.
- [`strided-layout-reduction`](strided_layout_reduction.md): Avoid implementing a non-last-dimension single-axis reduction by first doing `movedim(...).contiguous()` or an equivalent layout copy.
- [`pad-copy-row-col-tiling`](pad_copy_row_col_tiling.md): settles the pad multiple and block width that the search then tunes; apply it first when the kernel still needs the padded form.
