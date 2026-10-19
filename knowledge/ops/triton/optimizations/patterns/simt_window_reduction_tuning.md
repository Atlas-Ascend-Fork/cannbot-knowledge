---
type: Optimization
title: SIMT Window Reduction Tuning
description: 每个输出点映射到仿射布局固定输入窗口的 kernel 在 SIMT 路径上的调参方法论与反模式表。
tags: [task.optimization, topic.compute.reduction, topic.performance.analysis]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/simt-window-reduction-tuning.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: ['950']
---
# SIMT Window Reduction Tuning

## Summary

Tuning methodology for kernels that map **each output point** to a **fixed-size input window** over an **affine N-D layout** (e.g. NCDHW/NCHW), then **reduce** (sum, max, etc.) under **Ascend 950 `force_simt_only=True`**. Teaches how to **derive** dispatch, inner paths, and launch params from **structural features** — not from a specific op name. Pool-style ops are one common instance; the same signals apply to any op matching the shape below.

## Use When

Your kernel reduces a fixed-size input window for each output point, as in
pooling-style ops over NCDHW/NCHW layouts. The window position is an affine
function of the output coordinate, the kernel size is fixed at compile time,
and the inner loop does discrete per-window-element loads rather than dense
vector math. A typical example:

```python
start = out_coord * STRIDE - PAD        # affine output→input map
for tap in tl.static_range(KERNEL_D * KERNEL_H * KERNEL_W):
    acc += tl.load(x_ptr + base + start + tap, mask=in_bounds)
```

The kernel runs on Ascend 950 with `force_simt_only=True`, so this scalar,
index-heavy access is the intended lowering. This card is a tuning methodology
rather than a single rewrite: it applies when you must choose dispatch, inner
paths, and launch parameters across many shapes.

## Avoid When

- Not Ascend 950 SIMT, or compute-bound dense vector math dominates.
- Cube/matmul kernels, irregular gather indices, or value-dependent window sizes — none of these match the fixed affine window signature.
- Mixing **SIMT** and **non-SIMT scalar row** kernels in the **same module/process**.

---

## Method

Confirm the fit first: the window size must be a compile-time constant, the
output→input offset affine, and the hot path SIMT-lowered discrete access on
Ascend 950. The optimization core is to derive dispatch, inner paths, and
launch parameters from host-computed structural features — do not copy
thresholds from another op without re-benchmarking.

Tune one variable class per round:

```text
P0 Launch      → force_simt_only + single launch
P1 Dispatch    → flat 1D vs row×col 2D grid
P2 Inner path  → full interior vs boundary (mask / clip / include-pad norm)
P3 Geometry    → BLOCK, num_warps, static unroll depth
P4 Validation  → fresh process, full harness geomean
```

| Stage | Pass evidence | Revert if |
|-------|---------------|-----------|
| P0 | geomean up vs multi-launch | correctness fail |
| P1 | target shape bucket improves | small shapes regress |
| P2 | semantics match reference | boundary half-dtype regress |
| P3 | 507035 cleared | geomean drops |
| P4 | stable across two runs | single-case ×10 spike (co-JIT) |

### Rule: Derive routing from host-computed features

| Feature | How to compute |
|---------|----------------|
| Output spatial sizes | from stride, pad, ceil, dilation rules |
| `n_out` | product of output tensor shape |
| `window_vol` | product of fixed kernel sizes |
| `eff_span_*` | `dilation * (k - 1) + 1` per axis |
| `row_parallelism` | outputs sharing outer dims (for 2D grid) |
| `pad_any`, `ceil`, `dilated`, `half` | semantic / dtype flags |
| `window_fully_inside` | last window fits in input (use eff_span) |
| `reduce_kind` | cheap acc vs heavy compare+where+extra state |
| `norm_semantics` | e.g. include-pad in normalizer vs clipped volume only |

**Stack-pressure proxy:**

```text
stack_pressure ≈ window_vol × (mask_branches + extra_state_per_tap)
```

High when: boundary path, clip nest, include-pad normalizer, compare+index chain, half dtype, 2D vector tile.

### Rule: Route flat 1D vs row×col 2D grid by feature bucket (P1)

**Row×col helps when:** wide inner spatial dim + large `window_vol` + enough row parallelism + **cheap per-tap reduce**.

**Flat helps when:** narrow inner dim, low outer parallelism, or **heavy per-tap state** (compare + index + where chains).

**Routing:** start flat-only; enable row×col for a **named feature bucket**; bisect thresholds on harness geomean.

### Rule: Split the interior fast path from the boundary path (P2)

Interior fast path (`USE_FULL_INTERIOR` / host equivalent):

```text
interior iff no pad AND no ceil edge AND unit dilation
           AND window_fully_inside (eff_span)
```

Kernel: fixed `window_vol` scan, no per-tap masks.

Boundary path selection:

| Normalizer / semantics | Preferred inner | Note |
|------------------------|-----------------|------|
| Include virtual pad in norm volume | full nest + **coord masks** + **one-shot norm** | normalizer below |
| Clipped volume only (exclude pad from norm) | **clip-window** + closed-form volume | `simt-window-divisor-formula` |
| Dilation > 1 | coord masks only | no clip shortcut |
| Heavy compare + half + pad | coord masks over clip | stack depth |
| Compare + arg index | masks + fp32 compare + linear index | |

**Include-pad normalizer (once per lane):**

```python
norm_axis = max(min(start + K, in + PAD) - start, 0)
normalizer = product(norm_axes)  # fp32 when dividing
```

**Empty window:** output sentinel (e.g. 0); clamp normalizer to avoid div-by-zero.

Choose mask vs clip by **semantics first**, then A/B on harness if 507035 or geomean regression.

### Rule: Tier BLOCK, num_warps, and unroll depth by stack pressure (P3)

- **BLOCK** tiers with `n_out`; cap lower when `stack_pressure` high (often 512).
- **num_warps:** default 8; try 4 when stack_pressure high (boundary + half).
- **Row×col W tile:** pow2 BLOCK on Ascend; tier row tile with row_parallelism; cap rows on boundary paths.
- **Static unroll:** innermost kernel width only for small fixed k; never full N-D static unroll at large `window_vol`.
- **fp32** for accumulate/compare; store native dtype.

### Rule: Re-derive choices per reduce kind

| Feature | Cheap reduce (sum/mean) | Heavy reduce (max + index) |
|---------|-------------------------|----------------------------|
| Row×col | often wins on wide W + large vol | often loses |
| Boundary warps | usually 4 when not interior | 4 when half + boundary |
| Inner path | include-pad → mask; closed → clip | mask over clip on half pad |
| Scalar-row fallback in SIMT module | validate per module | high co-codegen risk |

**Discipline:** repair the architecture (single SIMT launch, correct inner
path) before tuning micro-parameters. Keep one device launch per invocation;
compare paths with `constexpr` branches inside one launch, or let host code
select different `@triton.jit` entry points per shape regime — do not add
extra launches to one invocation without measuring the total cost. Validate in
a fresh process and accept or reject each change by harness geomean.

---

## Optimization Points (source → evidence → failure)

| Point | Why | Verify | Failure |
|-------|-----|--------|---------|
| Single SIMT launch | launch tax | one kernel / forward | still bound on inner |
| force_simt_only | discrete path on Ascend 950 | profile + geomean | no gain |
| Interior fast path | skip masks | unpad cases faster | memory-bound |
| flat vs row×col | match parallelism | bucket geomean | small-shape regress |
| One-shot normalizer | no per-tap count | correct semantics | wrong output |
| mask vs clip | stack vs mask count | A/B boundary half | 507035 / geomean drop |
| Monolithic kernel | avoid co-JIT | stable fresh bench | one-case spike |
| No SIMT + scalar-row mix | codegen clash | never embed/import row | geomean collapse |

---

## Anti-Patterns (by trigger feature)

| Trigger | Anti-pattern |
|---------|--------------|
| Ascend 950 SIMT + overlapping W loads | inner-W slab gather (`window-slab-gather`) without re-proof |
| Any | global interior/boundary **multi-launch** |
| Small window_vol + low parallelism | forced row×col |
| Any | in-kernel `tl.where(interior, …)` split |
| Any | separate launch kernels per interior/boundary/clip |
| Large window_vol | full N-D static unroll → 507035 |
| SIMT module | scalar-row fallback |
| Bench session | mixed kernel architectures → co-JIT |

---

## Related Patterns

- [force-simt-only-discrete-access-950](./force_simt_only_discrete_access_950.md) — enable SIMT
- [logical-layout-tiling](./logical_layout_tiling.md) — outer flat index → layout tile
- [simt-window-divisor-formula](./simt_window_divisor_formula.md) — closed normalizer inner loop
- [window-slab-gather](./window_slab_gather.md) — inner-dim slab (usually not Ascend 950 SIMT)
