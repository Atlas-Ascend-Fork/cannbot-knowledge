---
type: Optimization
title: Scattered Transfer Batching
description: 索引搬运由零散小传输主导时，用 extract_slice/insert_slice 把可连续化的一侧批量化。
tags: [task.optimization, topic.data_movement.data_copy, topic.compute.indexing]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/scattered-transfer-batching.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Scattered Transfer Batching

## Summary

When indexed movement is dominated by small scattered transfers, use
`extract_slice` or `insert_slice` to batch the side that can become contiguous.
This can reduce global-memory transactions, but the final read/write direction
still determines whether the transfer is actually coalesced.

## Use When

A kernel rearranges elements through an index array — token reordering, sparse
permutation, or similar index-based movement — and each index drives its own
small scattered global load or store:

```python
for i in range(BLOCK):
    idx = tl.load(indices + i)
    tl.store(out_ptr + idx * D + offsets, row_i)  # one scattered transfer per index
```

These small scattered transfers dominate the kernel's global-memory cost. One
side of the movement — the reads or the writes — could be made contiguous by
staging a block of rows in UB.

Staging that side in UB batches many small scattered transfers into a few
contiguous ones.

## Method

Confirm the fit first: check from the code or a profile that many small
scattered transfers dominate, and identify which side of the movement can be
made contiguous.

The optimization core is to stage that side in UB with `extract_slice` or
`insert_slice`, so the kernel issues a few contiguous transfers instead of
many scattered ones. The other side stays scattered — this pattern can
coalesce only one direction.

### Rule: Coalesce contiguous reads with a batch load and `extract_slice`

When the source rows are contiguous but the destinations are scattered, load
a whole contiguous block into UB once. Extract each row from UB — a cheap
local operation — and store it to its scattered location:

```python
data = tl.load(x_ptr + block_start + data_offset)  # one contiguous load
for i in range(BLOCK):
    token = tl.extract_slice(data, [i, 0], [1, D], [1, 1])
    idx = tl.load(indices + i)
    tl.store(out_ptr + idx * D + tl.arange(0, D)[None, :], token)
```

### Rule: Coalesce contiguous writes with `insert_slice` and a batch store

When the destinations are contiguous but the sources are scattered, assemble
the scattered rows into a UB buffer and store the buffer once:

```python
buffer = tl.full((BLOCK, D), 0, dtype=x_ptr.type.element_ty)
for i in range(BLOCK):
    idx = tl.load(indices + i)
    row = tl.load(x_ptr + idx * D + tl.arange(0, D)[None, :])
    buffer = tl.insert_slice(buffer, row, [i, 0], [1, D], [1, 1])
tl.store(out_ptr + block_offset, buffer)  # one contiguous store
```

Choose the rule by access direction: batching the wrong side leaves the
expensive scattered transfers in place.

Discipline note: this pattern reduces the global-transfer count only when the
batched side actually becomes contiguous, and it does not reduce host launch
count. Keep the staged block within UB capacity — shrink the block if it does
not fit — and confirm the improvement with a profile rather than assuming it
from the source change.

## Related Patterns

- [discrete-access-ub-staging](./discrete_access_ub_staging.md): the load-side cousin — stage the whole gather source in UB and select on-chip; this card batches the contiguous side of an index-driven movement, including scatter stores.
- [gather-then-dense-compute](../operator_optimization/device_side_gather.md): decouples scattered row loads from a following dense compute by staging rows into a contiguous buffer first.
- [现有知识：单位置 False 的 tl.where 退化规避](../techniques/where_optimization.md)
