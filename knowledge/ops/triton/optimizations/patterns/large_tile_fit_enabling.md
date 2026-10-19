---
type: Optimization
title: Large-Tile Fit Enabling
description: 当有价值的大 tile 因额外临时量无法通过 UB 规划时，把等价不变量计算移到更小输入上，以配对实验解锁大 tile。
tags: [task.optimization, topic.memory, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/large-tile-fit-enabling.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Large-Tile Fit Enabling

## Summary

When a valuable large tile fails UB planning, inspect the extra temporaries created by calculations on the large tile. Move an equivalent invariant calculation to a smaller input tile when that can reduce the size or lifetime of temporary values; use a paired compile and correctness experiment to determine whether this unlocks the large tile.

## Use When

A larger tile would reduce repeated loop work, but the compiler rejects it
during UB planning / buffer allocation, and the source-level tensor sizes do
not explain the failure. The hot loop performs an elementwise scale, cast, or
mask on the large dot/reduction result:

```python
qk = tl.dot(q, k)          # large [BLOCK_M, BLOCK_N] fp32 tile
qk = qk * sm_scale         # a second large-tile operation lives here
```

The loop-invariant operation can be moved onto a smaller input instead (e.g.
pre-scale `q` once before the loop), which may reduce peak live UB enough for
the large tile to compile. This is a compiler-resource hypothesis: moving the
operation is not claimed to always reduce UB or improve performance. When it
works, the rejected large tile compiles and its loop-work savings unlock.

## Signals

### Code

- A dot produces a large tile such as `qk: [BLOCK_M, BLOCK_N]`, followed by another operation that may materialize or keep a second large value live.
- The same loop-invariant scalar is applied to every large result tile.
- A cast or layout conversion occurs after a large intermediate rather than before the operation that creates it.

### IR

- Memory planning reports a requested footprint above usable UB.
- The failing form contains two large values or a long live range around the dot result.
- After the rewrite, the compiler shows a smaller pre-dot temporary, a shorter dot-result live range, fewer overlapping buffers, or successful planning.

IR evidence strengthens the hypothesis, but a compile-only candidate is still useful when the source shapes and failure stage clearly identify the resource boundary.

## Method

Confirm the fit first: compilation of the candidate tile fails at UB planning
/ buffer allocation, and source shapes do not explain it. Write down the
sizes on both sides — the large result tile (e.g. FP32 `[256, 128]` = 128
KiB) versus the smaller input the invariant operation could move to (e.g.
BF16 `[256, 64]` = 32 KiB). The moved temporary must be materially smaller to
matter, and the large tile itself still exists; the win is removing the
*second* large-tile operation, not the large tile.

The optimization core is to move the loop-invariant operation off the large
result tile onto the smaller input:

```diff
+ q_scaled = (q * sm_scale).to(q.dtype)   # once, outside the loop
  for n0 in range(0, S, BLOCK_N):
-     qk = tl.dot(q, k)
-     qk = qk * sm_scale                   # second large-tile operation
+     qk = tl.dot(q_scaled, k)
      update_online_softmax(qk, v)
```

Then prove the coupling with a 2×2 control on the same shape, keeping the
host grid, inputs, precision contract, and benchmark case identical:

| Variant | Tile | Scale placement | Question answered |
|---|---|---|---|
| control | parent | on result | baseline |
| tile-only | large | on result | does the large tile fail without the enabler? |
| enabler-only | parent | pre-scaled input | does the enabler alone regress? |
| combined | large | pre-scaled input | does the large tile compile and pass now? |

Record the compile stage and correctness before any timing. If tile-only
fails while combined compiles and passes, classify the pre-scale as a
**fit enabler** for the large tile — not an independent speedup; confirm the
allocation or live-range change in IR when possible, and report the internal
UB cause as unconfirmed when IR does not show it. If different shapes need
different validated tiles, hand off to `tile-footprint-fitting` or `autotune`.

## Related Patterns

- [tile-footprint-fitting](../techniques/tiling.md): choose and compare tile sizes after this card identifies a legal candidate.
- [attention-visibility-mask-specialization](./attention_visibility_mask_specialization.md): separate loop-work reduction from UB-fit effects.
- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md): find invariant calculations that may be moved, without assuming a UB or performance benefit.
- [l2-stripe-capacity-tile-widening](./l2_stripe_capacity_tile_widening.md): size the widened tile against L2 stripe capacity once this card has established that the candidate tile is legal.
- [现有知识：三级 Tiling 层次与 UB 容量约束](../techniques/tiling.md)

## What To Verify After Applying

- The moved operation preserves dtype, rounding, tolerance, finite outputs, and recurrence semantics.
- The parent and candidate cover exactly the same logical work.
- The failure stage and target/compiler identity are recorded.
- The source shapes explain why the moved operation is smaller, and IR confirms the suspected allocation or live-range change when available.
- The candidate large tile compiles and passes correctness before performance is compared.
- The final report distinguishes observed compile success from the unconfirmed internal reason for that success.
