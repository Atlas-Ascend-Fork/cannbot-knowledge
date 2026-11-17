---
type: Optimization
title: 相邻 Store 合并
description: 合并可由同一 program 安全拥有的相邻输出写入，减少碎片化搬运与固定开销。
tags:
- task.optimization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/merge-adjacent-stores.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Merge Adjacent Stores Pattern

## Summary

Combine separate small `tl.store` operations into one wider store when the destination addresses form a continuous interval, so the NPU emits a single vector-friendly DMA write instead of multiple tiny transactions.

## Use When

A copy-heavy or store-heavy kernel writes its output through several small
`tl.store` operations whose destination addresses sit next to each other —
typically one store per loop iteration, or a few stores to adjacent sub-ranges
of one output block:

```python
for i in range(K):
    tl.store(out + base + i * SUB, vals_i)  # K small adjacent stores
```

Merging is safe when the written addresses form one continuous interval and
the per-element masks agree, and worthwhile when profiling or code inspection
shows the many small stores — not loads or compute — limiting throughput.

The rewrite merges them into one wide store: many small DMA transactions
become one vector-friendly write.

## Avoid When

- Destination addresses are not a continuous interval — merging would change semantics.
- Masks differ across the candidate stores in a way that changes correctness.
- The combined write would exceed UB capacity or register pressure for the active tile.

## Signals

### Code

- Multiple `tl.store` calls write to addresses that differ only by a small constant offset within a contiguous block.
- A loop emits one `tl.store` per iteration even though the outputs across iterations are adjacent.
- Store instructions outnumber load instructions significantly in a copy-heavy or epilogue-heavy kernel.

## Method

Confirm the fit first: the candidate stores must write a provably contiguous
address run with compatible masks, and the wider combined value must still
fit the active tile's UB and register budget.

The optimization core is to compute the values once and issue a single wide
masked store over the whole contiguous range instead of several small ones.

### Rule: Merge same-site stores to adjacent sub-ranges

When one program issues several stores to neighboring offsets of the same
output block, preserve its global base, widen the offset vector and store once.
Here `offs_lo = pid * (2 * HALF) + tl.arange(0, HALF)` and `out` still
points to the beginning of the complete output:

```diff
- tl.store(out + offs_lo, vals_lo, mask=offs_lo < n)
- tl.store(out + offs_lo + HALF, vals_hi, mask=offs_lo + HALF < n)
+ base = pid * (2 * HALF)
+ offs = base + tl.arange(0, 2 * HALF)
+ vals = combine(vals_lo, vals_hi)
+ tl.store(out + offs, vals, mask=offs < n)
```

### Rule: Replace per-iteration stores with one wide store

When a loop stores one small slice per iteration into adjacent addresses,
buffer the slices and store the whole run after the loop — only when all
slices fit live at once. Keep the same global `base` in both forms:

```diff
- for i in range(K):
-     offs_i = base + i * SUB + tl.arange(0, SUB)
-     tl.store(out + offs_i, compute_slice(i), mask=offs_i < n)
+ offs = base + tl.arange(0, K * SUB)
+ vals = compute_all_slices(...)  # values for the whole run, live together
+ tl.store(out + offs, vals, mask=offs < n)
```

With `HALF=4`, two programs must write `[0, 8)` and `[8, 16)` respectively.
For `n=13`, the second program writes only `[8, 13)`; no program owns
an address in another program's block.

### Rule: Keep the boundary mask exact

The merged store must reproduce the original per-element masking, including
the tail. Build the wide mask from the same bound the small stores used; do
not widen the store past the last valid element.

Merge one store group at a time and benchmark: the wider store should reduce
DMA write transactions without pushing the combined value past UB capacity
or disturbing other pipeline stages.

## What To Verify After Applying

- Confirm semantic equivalence: the merged store produces identical output values for all lanes.
- Check that the merged mask correctly handles tail and partial blocks.
- Benchmark to confirm the wider store reduces DMA transaction count without harming other pipeline stages.
