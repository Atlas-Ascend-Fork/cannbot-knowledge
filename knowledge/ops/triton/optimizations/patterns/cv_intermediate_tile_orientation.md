---
type: Optimization
title: Cube-Vector Intermediate Tile Orientation
description: 为跨越 L0C 到 GM 供 Vector 消费的 Cube 中间矩形选择朝向，使其沿融合扫描轴构成规则 row-major tile。
tags: [task.optimization, topic.data_movement.layout_transform, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/cv-intermediate-tile-orientation.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Cube-Vector Intermediate Tile Orientation

## Summary

Choose the orientation of Cube-produced rectangular intermediates that cross L0C-to-GM so Vector consumes a regular row-major tile along the fused scan axis, deferring any remaining transpose to the consumer Cube dots. The two orientations hold the same values; only fixpipe layout and Vector access order change.

## Use When

In a mixed Cube/Vector kernel (attention-style), a Cube dot produces a tile
that Vector work transforms row by row (softmax-like scale/mask/exp) before a
later Cube dot consumes it, and the producer dot emits the transpose of the
Vector-natural orientation:

```python
qkT = tl.dot(k, q.T)               # [64, 256]: scan axis (queries) is trailing
pT = tl.exp2(qkT - lse[None, :])   # Vector walks the long trailing axis
```

The same values are available in the Vector-natural orientation
(`tl.dot(q, k.T)` → `[256, 64]`), and profiling or IR attributes cost to the
Cube-to-Vector transfer (fixpipe) or to Vector walking the transposed tile.

## Avoid When

- The transpose is on the kernel's public output store rather than a Cube-to-Vector intermediate; use `result-tile-layout-alignment`.
- The mismatch is a GEMM operand's physical storage versus the math layout; use `implicit-transpose-elimination`.
- The candidate deletes, shares, or shortens Vector operations on an already-oriented tile; use `attention-intermediate-vector-work-reduction`.
- The candidate changes Cube/Vector issue order, multibuffer depth, or compile-option pipelining; use `software-pipeline` or `cv-compile-option-ablation-950`.
- The intermediate is square and the consumer accesses both orientations equivalently, or compile legality admits only one tile shape. Equal extents alone do not prove equal access order or broadcasts.

## Signals

### Code

- Producer dots use `tl.dot(k, q.T)` / `tl.dot(v, do.T)` to emit `[BLOCK_N, merge_M]`, then Vector applies `exp2`, mask, and broadcasts such as `lse[None, :]` or `delta[None, :]`.
- An equivalent rewrite uses `tl.dot(q, k.T)` / `tl.dot(do, v.T)` to emit `[merge_M, BLOCK_N]`, with row broadcasts `lse[:, None]` and consumer dots `tl.dot(ds.T, q)`.
- The fused scan-group extent (`merge_M`, often 256) is much larger than the resident Cube tile extent (`BLOCK_N`, often 64).

### Profile

- Fixpipe or L0C-to-GM time on the score-like intermediate is material on the hot path.
- Vector special-function or elementwise time scales with the long transposed trailing dimension.
- Cube waits on Vector softmax, mask, or `dS` of that intermediate even when later accumulation dots are themselves cheap.

### IR

- The lowered L0C dump or fixpipe tile is `[N, M]` (for example `[64, 256]`) rather than `[M, N]` (`[256, 64]`) for the same merge group.
- Vector lowering walks columns of a wide tile instead of rows of a tall tile for per-row scale, mask, or exp.

## Method

Confirm the fit first: both dot orientations compute the same values, the
current producer emits the transpose of the Vector-natural orientation, and
profiling or IR attributes cost to the Cube-to-Vector transfer or to Vector
walking the long trailing axis.

The optimization core: flip the producer dot so the Vector scan axis leads
the tile, and move the transpose onto the consumer Cube dots — Cube reads
transposed operands cheaply, Vector does not. Keep tile math, mask semantics,
dtypes, and fallback loops fixed while isolating the orientation change, and
keep the flip only when IR shows the fixpipe tile shape change and benchmarks
improve on the targeted shapes.

### Rule: Emit the Vector scan axis as the tile's leading axis

A backward `dK`/`dV` merge4 group keeps 64 resident key rows and scans 256 query rows. Both of the following compute the same pairwise values:

```python
# [64, 256] fixpipe orientation: scan group is the trailing axis
qkT = tl.dot(k, q.T)                 # [64, 128] @ [128, 256]
pT = tl.exp2(qkT - lse[None, :])
dsT = pT * (tl.dot(v, do.T) - delta[None, :])
dk += tl.dot(dsT.to(q.dtype), q)     # no extra transpose at consume time
```

```python
# [256, 64] fixpipe orientation: scan group is the leading axis
qk = tl.dot(q, k.T)                  # [256, 128] @ [128, 64]
p = tl.exp2(qk - lse[:, None])
ds = p * (tl.dot(do, v.T) - delta[:, None])
dk += tl.dot(ds.to(q.dtype).T, q)    # transpose moves onto the consumer Cube dots
```

Prefer the second form when Vector owns the 256-row scan group and the Cube-to-Vector transfer should match that row-major view. Keep tile math, mask semantics, dtypes, and fallback loops fixed while isolating the orientation change.

## Related Patterns

- [result-tile-layout-alignment](./result_tile_layout_alignment.md): align a kernel output accumulator with its public store layout, not a Cube-to-Vector intermediate.
- [implicit-transpose-elimination](./implicit_transpose_elimination.md): fix GEMM operand physical layout and compiler-injected operand transposes.
- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): shorten Vector work between Cube producer and Cube consumer after the tile orientation is chosen.
- [software-pipeline](./software_pipeline.md): inspect generated buffering and overlap; do not treat orientation as a schedule rewrite.
- [cv-compile-option-ablation-950](./cv_compile_option_ablation_950.md): ablate Ascend 950 Cube/Vector compile options independently of source tile axes.
- [现有知识：CV 融合方法论](../operator_optimization/cv_fusion.md)

## What To Verify After Applying

- Broadcast axes for scale, LSE, delta, and mask match the new leading dimension.
- Consumer dots still implement the same `dK`/`dV` (or equivalent) accumulation, including dtype casts.
- Fallback or non-merge paths are unchanged unless they share the same intermediate orientation.
- IR shows the claimed fixpipe tile shape change rather than only a source-level transpose.
- Correctness holds on exact-tile fast paths and on any remaining masked tails.
- Benchmarks improve on the targeted shapes; reject a flip that only moves cost onto consumer Cube transposes or UB spills.
