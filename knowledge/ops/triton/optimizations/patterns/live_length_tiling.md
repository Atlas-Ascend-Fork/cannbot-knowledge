---
type: Optimization
title: Live-Length Tiling
description: 按各轴实际存活逻辑长度选择 tile 宽度，替代遗留最大值或一刀切 2 的幂规则，避免 masked 空车道主导工作量。
tags: [task.optimization, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/live-length-tiling.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Live-Length Tiling

## Summary

Choose tile widths from the live logical length on each axis instead of a legacy maximum or blanket power-of-two rule, so masked lanes do not dominate loop iteration counts, transfer work, or vector-path work.

## Use When

A kernel picks a `BLOCK_*` tile width from a fixed cap or `next_power_of_2()` while a mask protects a much smaller valid length:

```python
BLOCK_H = next_power_of_2(width)   # e.g. 128 lanes for 80 valid
offs = tl.arange(0, BLOCK_H)
x = tl.load(ptr + offs, mask=offs < width)
```

Most lanes in each block then do padded work rather than useful work. Profiling shows LD/ST, scalar-loop, or transfer cost tracking the full tile width instead of the valid lane count. The oversized axis is a copy-like or indexed/masked access path that does not participate in `tl.dot`, cube alignment, or reduction-tree structure. The host already knows the shape and could choose a smaller tile or a different launch branch. Sizing the tile to the live valid length removes the padded-lane work instead of paying it on every iteration.

## Signals

### Code

- **`BLOCK_SIZE`**, **`BLOCK_M`**, **`BLOCK_N`**, or **`BLOCK_H`** is chosen from a cap or unconditional **`next_power_of_2()`** while the mask protects a much smaller live length.
- A copy-like path uses **`tl.max_contiguous(ptr, BLOCK)`** or similar contiguous-lane hints together with **masked `tl.load` / `tl.store`** on the final or inner block.
- Structured and flat launches reuse one tile heuristic even though their live lengths differ.
- Indexed globals use **`tl.load` / `tl.store` / `tl.atomic_*`** with per-lane masks, and the tile looks larger than the number of useful lanes.

### Profile

- Switching from a padded tile to a smaller exact-width tile lowers **MTE / DMA** time on the same logical workload.
- Small or narrow shapes pay unexpectedly high per-kernel latency.

### IR

- Indexed paths still show **`DiscreteMemAccess`** or extracted load/store structure after lowering.

## Method

Confirm the fit first: identify the live length on each tiled axis, not just the configured cap, and check from profile or IR that cost tracks the padded tile width rather than the valid lane count.

The optimization core is to choose tile widths from that live length so padded lanes stop dominating iteration counts, transfer work, and vector-path work. Measure each candidate and keep it only if IR shows loop bounds or static tile sizes shrink with the live length and the targeted profile metrics improve.

### Rule: Pick tile widths from a small measured candidate set

Compare padded-lane waste against grid growth across a few candidate widths instead of trusting one heuristic.

### Rule: Recompute the grid together with the tile

Grid size and any program-budget logic change with the tile width; never tune tile width in isolation.

### Rule: Prefer exact-length tiles on copy-only contiguous axes

For a copy-only contiguous axis, treat the exact length or `min(cap, length)` as the default candidate set, and treat `next_power_of_2()` as a measured alternative rather than the baseline. With a live width of 80 and one final masked block organized around `BLOCK_H`:

```diff
- BLOCK_H = next_power_of_2(80)   # 128: 48 masked lanes still moved
+ BLOCK_H = 80                    # tile matches the live width
```

On Ascend, the masked lanes in the padded block can still contribute to transfer and vector-path work even though the mask preserves correctness, so the exact-width tile often lowers MTE-heavy time. The same idea applies to indexed paths: even when **`DiscreteMemAccess`** remains in IR, shrinking the tile to the live length cuts wasted masked iterations and padded memory-op counts.

### Rule: Put shape-dependent tile policy in host dispatch

If one tile policy is only correct or profitable for certain shapes, encode that split at the host dispatch layer. When a small set of lengths, such as `K == 64` or `K == 128`, dominates production shapes, consider dispatching to length-specialized kernels so inactive padded branches disappear from the hot path.

## Avoid When

- The axis participates in **`tl.dot`**, cube alignment, fixed reduction-tree structure, or another backend-sensitive alignment contract.
- The real bottleneck is **atomic contention**, unrelated host overhead, or another phase outside the oversized-tile region.
- A smaller tile would explode program count past a launch or synchronization knee.
- The target rejects the needed non-power-of-two tile shapes, or the resulting specialization count is unacceptable.
- Runtime lengths vary too widely for shape-specialized dispatch to stay maintainable.

## What To Verify After Applying

- **IR**: loop bounds or static tile sizes shrink with the live length where expected.
- **Profile**: LD/ST, scalar, or transfer-heavy metrics move with the new tile instead of the old padded width.
- **Correctness**: tail blocks, masks, dtypes, and all dispatch branches still behave identically.
- **Compilation / caching**: the target accepts the chosen tile shapes and JIT specialization does not become a new problem.
- **Dispatch coverage**: specialized length branches and the generic fallback are all validated.

## Related Patterns

- [discrete-access-ub-staging](./discrete_access_ub_staging.md)
- [tile-footprint-fitting](../techniques/tiling.md)
- [ragged-tile-early-return](./ragged_tile_early_return.md)
- [现有知识：Block Size Scaling 优化模式](../operator_optimization/block_size_scaling.md)
