---
type: Optimization
title: 单 Program 多行处理
description: 将多个独立行交给同一 program，摊销行级固定开销并保持足够并行度。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/program-multiple-rows.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Program Multiple Rows Pattern

## Summary

Amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.

## Use When

The kernel computes each output row mainly from one input row (row-wise
LogSumExp, row norms, row softmax statistics). One Triton program currently
handles exactly one row, and the inner loop only tiles the row length `N`:

```python
pid = tl.program_id(0)           # one program per row
row_ptr = x_ptr + pid * stride   # narrow (1, BLOCK_N) tiles
```

Profiling or timeline views show many tiny programs relative to the row count
`B`, high scalar/control overhead, or under-filled vector work per program.
The pattern also applies when `N` fits a single tile (`BLOCK_N =
next_power_of_2(N)`, no `N` loop); judge by the actual tile footprint and
target measurements, not by `N` alone.

## Signals

### Code

- `program_id(0)` indexes **rows 1:1** (`pid_m` is the row index), and the inner loop only tiles **`N`**.
- Scalar helpers (`program_id`, pointer arithmetic per row) run once **per row**; vector units see **narrow** tensors (e.g. `(1, BLOCK_N)` loads).

### Profile

- **`aiv_scalar_ratio`** or scalar-related time is **disproportionately high** compared to useful vector math, for workloads where `B` is large enough that vector throughput should dominate.
- If **`aiv_mte2_ratio`** is **not** the sole dominant bucket, pure “double-buffer the loads” may be the wrong first lever; **program batching** can still help by making each program’s inner loop **wider** along rows.
- Frequent **barrier / wait** patterns tied to **many short programs** or **thin** vector blocks.
- **Note:** High **`BAR`** cycle counts alone are **not** a success metric; correlate with **wall time**, **op_statistic Avg**, and correctness.

## Method

Confirm the fit first: `program_id(0)` must index rows one-to-one, and the
profile must show per-program scalar or launch overhead that is material
relative to the vector math.

The optimization core is to make one program own `BLOCK_M > 1` rows, so
fixed per-program costs are amortized and vector tiles widen from
`(1, BLOCK_N)` to `(BLOCK_M, BLOCK_N)` while the single streaming pass over
`N` per program is preserved.

### Rule: Map a block of rows to one program

Treat `pid_m` as a block of rows instead of a single row index:

```diff
- pid_m = tl.program_id(0)              # one row per program
- row_ptr = x_ptr + pid_m * stride_xm
+ pid_m = tl.program_id(0)              # one block of rows per program
+ rows = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
+ row_mask = rows < B
+ row_ptrs = x_ptr + rows[:, None] * stride_xm
```

- Build **2D tiles**: `vals` has shape `(BLOCK_M, BLOCK_N)`; row-wise reductions use **`axis=1`** (max, sum), so running state such as `m`, `s` is `(BLOCK_M,)`.
- **Stores**: one scalar per row → `tl.store(y_ptr + rows * stride_ym, x, mask=row_mask)`.
- **Grid**: `grid = (triton.cdiv(B, BLOCK_M),)`.

For a row-wise LSE with fused activations, the shape is: masked load to
`(BLOCK_M, BLOCK_N)`, streaming LSE with `tl.max` / `tl.sum` on `axis=1`,
then fused elementwise ops and a masked store.

### Rule: Size BLOCK_M from vector width and co-tune with BLOCK_N

- Calculate rows per vector from the target/compiler-reported vector width divided by element bytes, then test nearby powers of two rather than treating one width as hardware-global.
- When widening `BLOCK_M`, reduce `BLOCK_N` so `BLOCK_M * BLOCK_N` and usable-UB demand remain comparable; this separates lane-fill benefit from a larger working set.

Discipline note: every selected or autotuned `BLOCK_M` must launch
`cdiv(B, BLOCK_M)` programs and cover every row exactly once. Keep this host
grid binding attached to each config when comparing candidates.

## Avoid When

- **Row-by-row `tl.static_range` unrolling**: the unrolled body grows with `BLOCK_M`, which can increase instruction-cache pressure and register use. Compare it with one native 2D `(BLOCK_M, BLOCK_N)` tile with `axis=1` reductions.
- **Indexed 2D reductions along `axis=1`**: `tl.argmax` or `tl.max(..., return_indices=True)` may lower poorly on some targets, while index-free `tl.max` / `tl.sum` can be cheaper. Keep the reduction index-free only when target IR and correctness checks support that choice; if indexed semantics are essential, retain a separate path.
- **Second full pass** over `x` for the same row (e.g. two-pass LSE) usually **increases global reads**; msprof often shows **more MTE / wait** unless the algorithm truly requires it. Prefer **single-pass streaming LSE** when numerically stable.
- **Ping-pong / multibuffer** without evidence of **MTE–vector overlap** can add **sync and UB** cost; treat as a **separate hypothesis** to validate.
- Do not conclude from **one** metric (e.g. `BAR` cycles) without **end-to-end** timing and comparable workload.

## What To Verify After Applying

1. **Correctness**: same dtypes, masks for `rows >= B`, and numerically stable reductions (e.g. LSE max-shift) unchanged in meaning.
2. **Benchmark**: compare **mean / geomean** with the same harness; use project **`compare-perf`** flow when available—avoid hand-computed speedups from raw logs.
3. **Profiler**: compare **`op_statistic` Avg** for the same op; note **Count** and tensor shapes. Optionally re-check **`op_summary`** vector/scalar/MTE mix.
4. **Sanity**: if `B` is tiny, **`BLOCK_M > 1`** may help little; if `B` is huge, launching **`cdiv(B, BLOCK_M)`** programs should visibly reduce launch/program overhead.
5. **Equal work**: confirm the baseline and every candidate process the same rows, and capture the selected `BLOCK_M`/`BLOCK_N` plus matching host grid before comparing performance.

## Related Patterns

- Complements **[`dual-vector-core-parallel`](dual_vector_core_parallel.md)**: `BLOCK_M` widens work **within** one program; `tl.parallel` splits **independent** subgraphs across vector cores—orthogonal when dependencies allow.
- [`logical-layout-tiling`](logical_layout_tiling.md): the generic version of restructuring flat indexing into structured tiling; this card specializes it to row-reduction kernels with one-row-per-program baselines.
- [`pad-copy-row-col-tiling`](pad_copy_row_col_tiling.md): the same row-blocking technique applied to pad/copy kernels, with pad-specific mask disciplines.
- Differs from **[`software-pipeline`](software_pipeline.md)**: multibuffer targets **load/compute overlap** along a tile loop; **`program-multiple-rows`** targets **program granularity** and **row batching**.
- Once one program owns adjacent rows, test whether their regular 2D loads or stores are better represented with **[`block-pointer-tiles`](block_pointer_tiles.md)**. Row ownership and transfer representation are separate decisions; neither requires a persistent physical-program mapping.: Use `tl.make_block_ptr` as a compiler-facing representation candidate when source semantics define a regular multidimensional tile but IR suggests that manual pointer expressions lower into unexpectedly scalarized, fragmented, strided, or transpose-heavy memory operations.
