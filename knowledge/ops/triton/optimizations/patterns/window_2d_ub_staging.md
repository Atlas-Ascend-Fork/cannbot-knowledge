---
type: Optimization
title: 2D Window UB Staging
description: 2D 采样 kernel（resize/gather-window/pooling 类）为每个输出点读多个重叠输入样本时，先整行 staging 进 UB 再片上取样。
tags: [task.optimization, topic.data_movement.memory_access, topic.memory]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/window-2d-ub-staging.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# 2D Window UB Staging

## Summary

For 2D sampling kernels (resize, gather-window, pooling-like) whose hot path reads multiple overlapping input samples per output point, stage one rectangular input block from global memory into UB per program, flatten it, and serve all window reads from UB via on-chip gather. Secondary wins: allocate the block with its final aligned row stride (removes compiler-inserted UB-to-UB densify copies), tighten the block bounds to the true input window, and use a 2D output tile to cut program count.

## Use When

Your kernel samples a 2D input with overlapping windows — resize,
gather-window, or pooling-like — so each output point reads several input
samples, and the hot loop issues one dynamic-index global load per sample:

```python
for tap in range(K):
    acc += w[tap] * tl.load(gm_ptr + row_off[tap] * in_w + col_off[tap])
```

The rewrite stages one rectangular input block into UB per program and
serves all window reads from it on-chip, turning many scattered global loads
into one contiguous copy.

## Avoid When

- One input sample per output and access is already row-contiguous — staging may not pay off.
- Input layout is non-contiguous; a rectangular GM→UB copy is invalid without reordering first.
- The profile is dominated by scalar control (select chains), not memory — see `scalar-latency-trap-removal`.
- A larger tile overflows UB or grows the staged block faster than it saves programs.

## Method

Confirm the fit first: the hot path issues per-sample global loads, and the
profile shows load/store work dominating.

The optimization core is: one rectangular GM→UB copy per program, allocated
with its final aligned row stride, flattened, and served by on-chip gather,
on a 2D output tile sized to cut program count without overflowing UB.

### Rule: Stage one input block per program

```python
tile = tl.load(gm_ptr + iy[:, None] * in_stride + ix[None, :], mask=mask_in, other=0.0)
flat = tl.reshape(tile, (IN_H * IN_W,))
val = tl.load(flat + off)   # lowers to an on-chip gather, not a global load
```

### Rule: Allocate the block with its final row stride

If the block's logical width differs from its allocated stride, the compiler
inserts a UB-to-UB densify copy before the gather. Set
`IN_W = align_up(logical_w, 8)` at allocation time and compute gather offsets
as `(y - in_y0) * IN_W + (x - in_x0)` with the same constant.

### Rule: Tighten block bounds to the true input window

Derive the block size from the output tile corner, scale, and window radius,
not from a loose fixed multiplier of the tile size.

### Rule: Enlarge the 2D output tile to cut program count

Use a `(BLOCK_H, BLOCK_W)` tile per program instead of flattening the output
plane onto a 1D axis. A larger tile does not reduce total gather work — wider
gathers per program offset the fewer programs — the win is fewer programs and
less GM→UB traffic. Keep the staged block within UB.

### Rule: Precompute periodic scalar weights only after the memory path is clean

If the memory path is clean but scalar select/polynomial chains still
dominate (e.g. bicubic phase weights), hoist periodic weights to host tables
or constexpr. See `scalar-latency-trap-removal`.

**Discipline:** change one lever at a time and verify each in IR and
end-to-end timing.

## Mode Notes

The memory and launch rules apply to every resize mode; modes differ in
dispatch conditions, block margins, and weight periodicity:

- **Nearest**: window radius 0 — skip staging unless a tile spans multiple input rows.
- **Bilinear** (2×2): staging with a small block; phase tables rarely pay off with only 2 taps.
- **Bicubic** (4×4): the canonical stage + gather case; its separable horizontal+vertical passes are the template for any separable filter.
- **Area** (integer downsample): a box filter — one GM→UB tile per output block, accumulate in UB, single write; this is the template for pooling-like ops.

## What To Verify After Applying

- One GM→UB copy per program; no UB-to-UB densify copy before the gather.
- Gather row-step constant equals the allocated `IN_W`.
- Program count and GM→UB bytes are down; end-to-end latency improved.
- Reference match on corners, up/down sampling, and every dispatched branch.

## Related Patterns

- [window-slab-gather](./window_slab_gather.md): the same stage-then-gather idea for window reductions along the innermost dimension.
- [discrete-access-ub-staging](./discrete_access_ub_staging.md): stage a contiguous range in UB, then select on-chip.
- [pad-copy-row-col-tiling](./pad_copy_row_col_tiling.md): row-column tiled copy kernels.
- [scalar-latency-trap-removal](./scalar_latency_trap_removal.md): scalar-side cleanup after the memory path is clean.
- [现有知识：离散访存 UB staging 通用形态](./discrete_access_ub_staging.md)
