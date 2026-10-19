---
type: Optimization
title: Window Slab Gather
description: 沿最内连续空间维的固定窗口归约先加载一个 W_SLAB 长条，再从长条内片上 gather 各窗口，消除逐窗口重复读。
tags: [task.optimization, topic.data_movement.memory_access, topic.compute.reduction]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/window-slab-gather.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Window Slab Gather

## Summary

For **fixed-window reductions** along the **innermost contiguous spatial dimension** (NCHW-style: often **W**), load one **slab** of length **`W_SLAB_LEN = STRIDE_W * (BLOCK_OW - 1) + KERNEL_W`** at **`w_abs_min = ow_pid * BLOCK_OW * STRIDE_W - PAD_W`**, then **`tl.gather(slab, STRIDE_W * arange(BLOCK_OW) + kw)`** per **`kw`** instead of many **`start_w + kw`** masked loads. Higher rank differs only in outer loops over remaining spatial axes. **Adoption gate:** hot path must show **`W_SLAB_LEN` load + gather**.

**Ascend 950 SIMT (`force_simt_only=True`):** this slab path can lose to a discrete SIMT flat or row×col path because the gather adds work. Do not apply on Ascend 950 SIMT unless a matched target-harness comparison proves it helps.

**Not op-specific** — any affine sliding-window reduce with overlapping taps along the innermost dim; pool ops are the canonical example.

## Use When

The kernel computes a fixed-window reduction (mean, max, or similar) along
the innermost contiguous dimension of an NCHW-style tensor — pooling is the
canonical case. Each program owns a block of adjacent output columns and
loops over the window positions with one masked global load per step:

```python
for kw in range(KERNEL_W):  # one narrow masked load per window position
    v = tl.load(x_ptr + base + (start_w + kw) * stride_w, mask=ow_mask, other=0.0)
    acc += v
```

Adjacent output windows overlap, so the same input columns are reloaded from
global memory once per window position. Because the input columns are
regularly strided, one contiguous input range covers every window the
program owns.

The rewrite loads that whole range once and gathers each window position
from it on-chip, so overlapping columns are loaded once instead of
`KERNEL_W` times.

## Avoid When

- **Ascend 950 SIMT fixed-window reduce (`force_simt_only=True`)** — see the **Anti-Patterns** table in **`simt-window-reduction-tuning`**; the gather can lose to SIMT flat/row×col + coordinate-mask paths, so require a matched target-harness comparison before applying W-slab here.
- **`W_SLAB_LEN`** exceeds **UB / compiler** or **gather** limits—**reduce `BLOCK_OW`** or use **`USE_W_MASKED_SLAB`** / non-slab branches for that shape.
- **Host predicates** for **`USE_W_SLAB_LOAD`** are wrong (windows not fully inside input, pad misclassified)—always **diff against the framework reference**.
- **Tail tiles:** **`out_w % BLOCK_OW != 0`** requires **`ow_mask`** on **store** and usually **disables full-tile slab branches** unless tail handling is explicit.
- **Max-like reductions** with **`return_indices`**, **dilation**, or extra validity state — W-slab may help **loads** only; compare/index update needs a separate design and full geomean proof.
- **Layout** is not **W-contiguous** per row (fix with **`contiguous()`** or a different pattern).
- **Ascend 950 SIMT discrete window reduce** — follow **`simt-window-reduction-tuning`** (single launch, feature-derived dispatch/inner path) before W-slab; use **`simt-window-divisor-formula`** only when normalizer uses **clipped volume only**, not as default for all pad cases.
- **One failed gather attempt** on device—treat as **implementation bug**, not "pattern invalid"; see **Failure Playbook** below before abandoning gather.

## Signals

### Code

- **Baseline:** **`for kh`** (and **`for kd`** in 3D) with **`for kw`** doing **`tl.load(..., mask=window_mask)`** per **`kw`** on W.
- **Target:** per **`(kd, kh)`**, one **`tl.load`** of **`W_SLAB_LEN`** columns, then **`KERNEL_W`** **`gather`**s into **`BLOCK_OW`** lanes.
- **Host constexpr flags** (names illustrative): **`USE_W_SLAB_LOAD`**, **`USE_W_MASKED_SLAB`**, **`NO_PADDING_FASTPATH`**, **`FULL_W_TILE`**, **`BLOCK_OW`**, **`W_SLAB_LEN`**.

### Profile

- Many **discrete / narrow LD** ops on the pooling kernel name; **Avg** improves when IR shows fewer per-`kw` GM touches.
- **High `aiv_scalar_ratio`** alone does **not** mean "skip slab"—often means **add boundary specialization**, not **drop gather**.

## Method

Confirm the fit first: profiling or IR must show the repeated per-`kw` narrow loads on the hot path, and the window geometry must overlap (`STRIDE_W < KERNEL_W` or `BLOCK_OW > 1`). The optimization core is: one program owns `BLOCK_OW` adjacent output columns; for each `(kd, kh)` it loads one contiguous slab of `W_SLAB_LEN` columns covering all those windows, then gathers per `kw` into a `BLOCK_OW`-wide accumulator. Overlapping columns are loaded from global memory once instead of once per window.

### Rule: Replace per-`kw` loads with one slab load plus per-`kw` gather

```diff
- for kw in range(KERNEL_W):
-     v = tl.load(x_ptr + base + (start_w + kw) * stride_w, mask=ow_mask, other=0.0)
-     acc += v.to(tl.float32)
+ col = w_abs_min + tl.arange(0, W_SLAB_LEN)      # full-tile branch may drop the mask
+ slab = tl.load(x_ptr + base + col * stride_w, mask=(col >= 0) & (col < in_w), other=0.0)
+ lane_offsets = STRIDE_W * tl.arange(0, BLOCK_OW)
+ for kw in range(KERNEL_W):
+     acc += tl.gather(slab, lane_offsets + kw, axis=0).to(tl.float32)
```

With `BLOCK_OW = 4`, `STRIDE_W = 2`, `KERNEL_W = 3`, the slab is 9 columns and the three gathers hit indices `[0,2,4,6]`, `[1,3,5,7]`, `[2,4,6,8]` — the overlapping columns are loaded once. If `tl.gather` faults on `f16`/`bf16`, convert the slab to `f32` before the gather and accumulate in `f32`; validate numerics for both average and max.

### Rule: Keep tile geometry consistent

| Symbol | Definition |
|--------|------------|
| **`BLOCK_OW`** | Output columns per program along W; prefer **`out_w % BLOCK_OW == 0`** on slab branches (**`FULL_W_TILE`**). |
| **`W_SLAB_LEN`** | **`STRIDE_W * (BLOCK_OW - 1) + KERNEL_W`** — span of input columns touched by the OW tile. |
| **`w_abs_min`** | **`ow_pid * BLOCK_OW * STRIDE_W - PAD_W`** (+ region W offset if pooling a subtensor). |
| **`lane_offsets`** | **`STRIDE_W * tl.arange(0, BLOCK_OW)`** — gather indices for each output lane at fixed **`kw`**. |

**Do not** mix ad-hoc "strip" lengths (e.g. **`block_ow - 1` without `STRIDE_W`**, or per-lane **`start_w + kw`** as gather base) with the table above—common cause of **UB OOB** on Ascend.

### Rule: Gate slab branches with host constexpr predicates

| Branch | Enable when | Kernel behavior |
|--------|-------------|-----------------|
| **`USE_W_SLAB_LOAD`** | **Zero pad** (or pad only outside W), **`FULL_W_TILE`**, every window **fully inside** unpadded input (no partial D/H/W window) | Unmasked slab **`tl.load`**, then **`gather`**. |
| **`USE_W_MASKED_SLAB`** | **`FULL_W_TILE`**, but slab columns can be **OOB** (padding / ceil on W) | **`col = w_abs_min + arange(W_SLAB_LEN)`**, **`mask = (col >= 0) & (col < in_w)`**, **`load(..., mask=, other=0)`**, then **`gather`**. |
| **`NO_PADDING_FASTPATH`** | No pad, not eligible for slab, or **tail / partial window** | Per-**`kw`** vector **`tl.load`** with **`ow_mask`** only. |
| **Generic boundary** | **`ceil_mode`**, partial windows on D/H/W | Keep **safe indices + `window_mask`** per **`kw`**; **do not** force slab. |

Pick **`BLOCK_OW`** from **`out_w`** with a **small candidate list** (e.g. 128…1) favoring **divisors of `out_w`** when **`out_w`** is large; cap tile size for UB. **Do not** jump tile sizes arbitrarily (e.g. 8→32) without checking **`W_SLAB_LEN`** and **`FULL_W_TILE`**.

### Rule: Choose the grid conservatively

- **2D:** **`(batch * channels * out_h, cdiv(out_w, BLOCK_OW))`** — one logical **`oh`** per **`program_id(0)`** row bundle.
- **3D:** fold **`out_d * out_h`** into the row axis; the **W slab is unchanged**.
- **Avoid** folding **many `oh` (or `od×oh`) into one program** while also expanding an **H-slab** loop unless IR/profile proves benefit—launch count drops but **per-program GM traffic** can explode.
- Pair with **`program-multiple-rows`** when consecutive flat spatial rows can share enough setup to amortize slab overhead.

### Discipline note

Do not mark this pattern "done" if the final kernel has **zero `tl.gather`** on the hot path, or if IR shows **`memref.copy`** loops without consumption. Interior/boundary output splitting can combine with slab on **non-SIMT** paths; on **Ascend 950 SIMT** prefer single-kernel `constexpr` branches over stacking region splits with slab (see the **Anti-Patterns** table in **`simt-window-reduction-tuning`**).

## Failure Playbook

| Symptom | Likely cause | Action (before abandoning gather) |
|---------|--------------|----------------------------------|
| **UB / vec address OOB** | **`W_SLAB_LEN`** mismatch; **`gather` index ≥ slab length**; wrong **`w_abs_min`**; **`BLOCK_OW`** vs tail mask | Recompute the geometry table; enforce **`FULL_W_TILE`** on slab branches; shrink **`BLOCK_OW`**. |
| **Sync / illegal instruction** | **`gather`** on unsupported dtype | **`extf` slab to `f32`** before **`gather`**. |
| **Correctness drift** | Slab branch enabled with **partial D/H/W** windows | Disable **`USE_W_SLAB_LOAD`**; use **masked slab** or **generic** path. |
| **No perf gain** | Hot path still **per-`kw` load** (gather optimized away) | Inspect IR; fix branches so **slab path actually runs**. |
| **Regression on deep shapes** | Extra **region launches** without slab on interior | **Gate splits**; keep **slab on large interior regions**. |

**Do not** conclude "slab-gather invalid on Ascend" from a single failed attempt without completing this checklist and verifying IR on a failing case.

## Related Patterns

- `gather-load`: Stage contiguous data in UB before applying indirect indexing or gather.
- [discrete-access-ub-staging](./discrete_access_ub_staging.md): Stage a contiguous range into the Unified Buffer first, then use on-chip indexing (`tl.gather` or equivalent) to select target values, rather than loading directly from global memory through discrete indices.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): Amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.
- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md) (supporting lens for boundary math—not a substitute for W staging): Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.
- [simt-window-reduction-tuning](./simt_window_reduction_tuning.md) — Ascend 950 SIMT fixed-window tuning (use before W-slab on `force_simt_only` paths): Use for Ascend 950 SIMT fixed-window reductions after enabling SIMT launch mode.
- [simt-window-divisor-formula](./simt_window_divisor_formula.md) — closed normalizer inner loop; not the default include-pad path on Ascend 950 SIMT: Use closed-form clipped bounds when full-window masked counting is costly.

## What To Verify After Applying

- **Correctness:** framework **`avg_pool{2,3}d` / `max_pool{2,3}d` (values)** — **padding**, **ceil**, **divisor_override**, **count_include_pad**, **tail `out_w`**.
- **Pattern applied:** IR or source shows **`W_SLAB_LEN` load + `gather`** on the profiled hot case—not only region splits or fastpaths.
- **Benchmark:** **Avg / geomean** vs baseline; watch shapes with **many sub-launches** (depth × boundary bands).
- **Numerics:** **fp16/bf16** with **`f32` gather staging** if used.
