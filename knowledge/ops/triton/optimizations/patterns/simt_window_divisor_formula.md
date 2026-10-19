---
type: Optimization
title: SIMT Window Divisor Formula
description: SIMT 路径上固定窗口归约的内层结构修复：按窗口边界推导除数闭式，替代全窗口 masked 计数。
tags: [task.optimization, topic.compute.reduction, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/simt-window-divisor-formula.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: ['950']
---
# SIMT Window Divisor Formula

## Summary

**Inner-loop structural repair** for **fixed-window reductions** over **affine layouts** on **SIMT paths**: compute each output window's **clipped input bounds once**, use a **closed-form window volume** as normalizer (e.g. mean divisor), and iterate **absolute coordinates inside the clip** instead of scanning the full `KERNEL_*` cube with per-tap validity masks and runtime counting.

**Pattern signature:** constexpr `KERNEL_D/H/W` loops + per-tap `valid_*` / `safe_*` masks + **`count += tl.where(mask)`** inside the nest for normalization.

**Not op-specific** — applies whenever normalization uses **clipped tap volume** (exclude virtual pad from the normalizer). Pool-style `count_include_pad=False` is the canonical example.

**Relationship to `simt-window-reduction-tuning`:** that card owns outer dispatch, interior fast path, and mask vs clip routing. Use **this card** when normalizer semantics are **closed volume** (`d_len × h_len × w_len` from clip bounds). When normalizer must **include virtual pad extent**, prefer coordinate-mask + one-shot normalizer in the tuning card — A/B on harness before assuming clip is faster.

## Structural Repair Precedence

1. **Outer structure**: flat `numel(out)` + hot-path coordinate decode → `logical-layout-tiling`.
2. **Launch mode**: Ascend 950 scalar/index dominated → `force-simt-only-discrete-access-950`.
3. **Dispatch / inner routing**: `simt-window-reduction-tuning` — single launch, flat/row×col, interior path, mask vs clip by semantics and stack_pressure.
4. **Inner structure (this card)**: **closed normalizer** — clip bounds + closed-form volume; no per-tap counting.
5. **Inner-W slab**: `window-slab-gather` on **non-SIMT** paths only when profile proves slab+gather wins.

## Use When

A pooling-style kernel — fixed K_D×K_H×K_W window per output, regular
strides — running in SIMT launch mode divides each output by the number of
valid window elements: near the borders the window is clipped and the
divisor shrinks (avg-pool with `count_include_pad=False`). The inner loops
scan the full window and build that divisor by counting valid elements one
by one at runtime:

```python
for kw in range(KERNEL_W):
    w = start_w + kw
    valid_w = (w >= 0) & (w < in_w)
    mask = valid_d & valid_h & valid_w
    acc += tl.load(x_ptr + off, mask=mask, other=0.0)
    count += tl.where(mask, 1, 0)   # divisor accumulated per window element
```

The rewrite computes each output's clipped window bounds once, derives the
divisor from a closed-form formula, and iterates only inside the clipped
region — no per-element masks, no runtime counting.

## Avoid When

- **SIMT is not enabled yet** — apply `force-simt-only-discrete-access-950` first on Ascend 950 instead of using this pattern as a pre-SIMT cleanup.
- The kernel is on an **HIVM W-slab** or other non-SIMT compile path where `force_simt_only` is off or incompatible.
- Indices are value-dependent or the window is not a fixed affine span (true gather/scatter with irregular offsets).
- The kernel is already dominated by Cube/matmul work; scalar window bookkeeping is not the bottleneck.
- **Include-pad normalizer** is required — use coordinate-mask + one-shot normalizer (the interior/boundary path rule in `simt-window-reduction-tuning`) unless harness A/B proves clip wins.
- Applying clip-window would require dynamic loop trip counts per lane that the backend cannot lower safely, and the fallback kernel-index path is already fast enough on the current SIMT launch.
- You are about to abandon or have not finished validating the SIMT-only launch (compile `507035` repair, correctness) — stabilize SIMT first.

## Signals

### Code

- Innermost work is **`for kw in range(KERNEL_W):`** with **`w = start_w + kw`**, then **`valid_w = (w >= 0) & (w < in_w)`** and **`safe_w = tl.where(valid_w, w, 0)`**.
- Average pooling uses **`valid_count += tl.where(window_mask, 1, 0)`** or **`padded_count += ...`** inside the `kd/kh/kw` loops.
- **`start_* = o* * STRIDE_* - PAD_*`** is computed once per output lane, but clip bounds are **not** reused for divisor and loads consistently.
- **`x_base = n * stride_n + c * stride_c`** is recomputed inside every kernel tap instead of before the inner loops.

### Profile

- Profile row is for a kernel already launched with **`force_simt_only=True`** (or documented SIMT-only round).
- High **`aiv_scalar_ratio`** on the SIMT kernel; math is mostly load + reduce + normalize.
- Many compare/mask/where operations relative to useful loads, especially on padded or `count_include_pad=False` cases.
- Gains from SIMT-only launch and block tuning have plateaued while the inner loop body remains mask-heavy.

## Method

Confirm the fit first: the kernel is already launched with
`force_simt_only=True` (or an equivalent validated SIMT-only round), the
normalizer semantics exclude virtual pad from the volume, and the inner
loops still scan the full `KERNEL_*` window with per-tap masks and runtime
counting. Check all three before touching the loop body.

The optimization core is to compute each output lane's clipped input bounds
once, derive the normalizer as a closed-form product of clipped lengths, and
iterate absolute input coordinates inside the clip. This replaces an
O(window_volume) counting accumulation (`valid_count += 1`) with an O(1)
algebraic formula derived from the same clip bounds used for the loads.

### Rule: Compute clip bounds once per output lane

For each output coordinate, form the padded logical window
(`start_* = o* * STRIDE_* - PAD_*`) and clip it to the input tensor:

```python
tstart_d = tl.maximum(start_d, 0)
tend_d = tl.minimum(start_d + KERNEL_D, in_d)
d_len = tl.maximum(tend_d - tstart_d, 0)   # same shape for h and w
```

Empty window (`d_len == 0` or `h_len == 0` or `w_len == 0`): leave the
accumulator at zero and set the divisor fallback so `0 / 1 = 0`, matching
reference early-return behavior. On row-column tiles, reuse the same
formulas with broadcast shapes `(BLOCK_ROWS, 1)` and `(1, BLOCK_SIZE)`.

### Rule: Derive the divisor in closed form before the load loops

Do not count taps inside the `kd/kh/kw` loops. Build the divisor from clip
bounds, honoring the override and include-pad branches:

```python
if HAS_DIVISOR_OVERRIDE:
    divisor = DIVISOR_OVERRIDE
elif COUNT_INCLUDE_PAD:
    divisor = padded_d_len * padded_h_len * padded_w_len   # pre-clip spans
else:
    divisor = d_len * h_len * w_len
divisor = tl.where(divisor > 0, divisor.to(tl.float32), 1.0)
```

For interior tiles with `padding=0` and fully in-bounds windows, this
collapses to the constant `KERNEL_D * KERNEL_H * KERNEL_W`.

### Rule: Iterate absolute coordinates inside the clip

Replace kernel-offset iteration with absolute clipped input indices, and
hoist the per-lane base offset out of the loops:

```diff
 x_base = n * stride_n + c * stride_c
-for kd in range(KERNEL_D):
-    in_d_index = start_d + kd
-    valid_d = (in_d_index >= 0) & (in_d_index < in_d)
-    safe_d = tl.where(valid_d, in_d_index, 0)
-    ...
-    valid_count += tl.where(window_mask, 1, 0)
+for kd in range(KERNEL_D):          # constexpr upper bound
+    ti = tstart_d + kd
+    d_ok = kd < d_len               # skip taps outside this lane's clip
+    off = x_base + ti * stride_d + ...   # hi/wi terms likewise
+    acc += tl.load(x_ptr + off, mask=lane_mask & d_ok & h_ok & w_ok, other=0.0)
+tl.store(..., acc / divisor, mask=lane_mask)
```

With loads expressed as `tstart + kd` and guarded by `kd < d_len`, the
per-tap `valid_*` / `safe_*` pairs disappear. Keep `range(KERNEL_D)`
constexpr because clip lengths differ per lane; this is the practical
equivalent of a clipped `for (ti = tstart; ti < tend; ++ti)` loop under
SIMT divergence. Border outputs still need the `kd < d_len` guards — do not
expect mask-free border lanes. On Ascend, prefer
`tl.zeros([BLOCK], dtype=tl.float32)` over `tl.zeros_like(..., dtype=...)`
when creating divisor tensors.

### Rule: Add fast paths only inside the single SIMT launch

| Fast path | Guard | Effect |
|-----------|-------|--------|
| Constant divisor | `padding=0`, window fully in bounds, include-pad, no override | `divisor = KERNEL_D*KERNEL_H*KERNEL_W` |
| No length masks | same guard | drop `d_ok/h_ok/w_ok`; inner loads become unmasked |
| Interior / boundary split | mixed tiles | single-kernel `constexpr` branches; do not add a global multi-launch on Ascend 950 SIMT (see `simt-window-reduction-tuning`) |

Discipline: keep `force_simt_only=True` unchanged through this inner repair
unless compile or correctness forces a rollback. After the structural
change, retune `BLOCK_*`, grid decomposition, and `num_warps` on the same
SIMT launch, and benchmark interior-heavy and padding-heavy shapes
separately before keeping the rewrite.

## Failure Modes And Anti-signals

- Using **post-clip lengths** for normalizer when **include-pad semantics** apply — wrong; use one-shot normalizer from padded extent.
- Applying clip for **heavy compare + half pad** without geomean proof — often loses to coordinate mask on Ascend 950 SIMT.
- Applying only closed-form divisor but leaving kernel-index + `valid_*` loops — partial gain only.
- Assuming clip-window removes all masks on **border outputs**; edge lanes still need `kd < d_len` guards.
- Applying this pattern on a **non-SIMT** launch or replacing the SIMT path with W-slab without measurement — may regress or conflict on compile path (HIVM slab vs SIMT-only).
- Nested `@triton.jit` helpers that use unsupported APIs (`tl.zeros_like(..., dtype=...)`) on Ascend.

## What To Verify After Applying

- Correctness vs framework reference: padding, closed vs include-pad normalizer, ceil edges, normalizer override, empty windows.
- Inner hot path no longer contains **`valid_count +=`** / **`padded_count +=`** in `kd/kh/kw` loops.
- Clip bounds match CUDA reference on sampled outputs (compare against manual golden for one lane).
- Benchmark on representative JSON cases: interior-heavy shapes vs padding-heavy shapes separately.
- Round record states SIMT was already enabled (`force_simt_only=True` or equivalent) before this inner repair.
- Retune `num_warps` / block sizes on the **same** SIMT launch after the structural change.
- Document whether W-slab was considered and rejected or deferred (only relevant if SIMT is abandoned).

## Related Patterns

- [logical-layout-tiling](./logical_layout_tiling.md) — outer output traversal / row-column tile before SIMT inner-window repair: Use layout-aware tiles instead of per-lane div/mod coordinate decoding.
- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md) — hoist `x_base`, masks, and bounds; closed-form divisor is algebraic LICM plus counting elimination: Apply **Loop-Invariant Code Motion (LICM)** to Triton kernels: move computations that do **not** depend on the loop induction variable out of the loop, so each iteration performs only the minimal work that truly varies.
- [force-simt-only-discrete-access-950](./force_simt_only_discrete_access_950.md) — **required predecessor** on Ascend 950: enable and validate SIMT-only launch before inner-window repair
- [simt-window-reduction-tuning](./simt_window_reduction_tuning.md) — dispatch, interior path, mask vs clip routing: Use for Ascend 950 SIMT fixed-window reductions after enabling SIMT launch mode.
- [window-slab-gather](./window_slab_gather.md) — inner-W slab on **non-SIMT** paths: For **fixed-window reductions** along the **innermost contiguous spatial dimension** (NCHW-style: often **W**), load one **slab** of length **`W_SLAB_LEN = STRIDE_W * (BLOCK_OW - 1) + KERNEL_W`** at **`w_abs_min = ow_pid * BLOCK_OW * STRIDE_W - PAD_W`**, then **`tl.gather(slab, STRIDE_W * arange(BLOCK_OW) + kw)`** per **`kw`** instead of many **`start_w + kw`** masked loads.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md) — drop `d_ok/h_ok/w_ok` when tile is fully interior: Split exact-tile hot paths from generic masked kernels when dispatch-time shape guards can prove there are no tail tiles, so Ascend lowering can avoid boundary-only masks, padding values, block-pointer `boundary_check`, and related control branches.
- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md) — remove redundant `safe_*`, narrow masks, and unsupported APIs: Remove scalarizing constructs that block vector hardware utilization on Ascend NPU, including unnecessary scalar control flow, loop-carried pointer recurrences, modulo addressing, narrow masks, and int64 arithmetic on vector paths.
- [algebraic-optimization](./algebraic_optimization.md) — closed-form divisor is an algebraic replacement for incremental counting: Apply mathematical identities and semantics-preserving rewrites to reduce redundant memory passes, full data scans, or live ranges before micro-tuning loads.
