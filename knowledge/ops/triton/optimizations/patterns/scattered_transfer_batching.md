---
type: Optimization
title: 零散传输批量化
description: 把索引驱动的零散传输改为连续片段批量搬运，并验证合并、聚合与必要同步的边界。
tags:
- task.optimization
- topic.data_movement.data_copy
- topic.compute.indexing
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/scattered-transfer-batching.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-11-17T03:37:03Z'
platforms:
- a2
- a3
- '950'
---

# Scattered Transfer Batching

## Summary

Batch the contiguous side of indexed movement in UB to reduce small global
transfers. When source and output locality follow different logical axes, a
small local tile can batch reads along one axis and reassemble writes along
the other. For a complete permutation of destination rows, an inverse map can
change ownership from source rows to contiguous output tiles: gather source
rows, compute locally, and write data and secondary outputs densely. Choose the
direction from the transfer bottleneck and include inversion cost.

## Use When

A kernel rearranges rows through an index array, and each index drives its own
small scattered global load or store. These small scattered transfers are a
large share of the kernel's global-memory cost. One or more of these situations
apply:

- **One side can become contiguous**: the reads, or the writes, could be made
  contiguous by staging a block of rows in UB.
- **Source and output axes differ**: adjacent source rows lie along one logical
  axis while adjacent output rows lie along another, so handling one output row
  at a time leaves both sides scattered. A small tile spanning those axes fits
  in UB.
- **The destination map is complete**: a producer already builds a complete
  destination map, and a later consumer rereads it to recover source rows before
  it can own contiguous output tiles. The producer has both coordinates at its
  existing store, so the inverse is derivable there.

## Signals

### Code

- Source-owned programs load a row once and scatter its transformed data and
  per-row or per-block secondary outputs to several destination rows.
- A forward route map gives each consumed destination exactly one writer; the
  source row is recoverable from a flattened route and its expansion factor.
- Indexed row loads can feed a native output tile whose last axis is contiguous,
  so the stores need no destination-dependent row addresses.
- Output-order traversal separates neighboring source rows, while a tile across
  two logical axes exposes adjacent reads and adjacent writes in different
  orders.
- Several weighted source streams feed each output row, and at least one stream
  has adjacent source indices within that tile.

### Profile

- Transfer counters show small scattered transfers on the stores, or on the
  loads, while the opposite side is already contiguous.

### IR

- Indexed destination stores lower to many small transfers or to scalar address
  and control work instead of wide contiguous stores.

## Method

Confirm the fit first: check from the code or a profile that many small
scattered transfers dominate, and identify which side of the movement can be
made contiguous.

Stage the selected side in UB with `extract_slice` or `insert_slice`, or gather
directly into a native tensor tile when the compiler provides that layout.
The other side stays scattered. With a complete destination permutation,
inverse routing can change which side becomes contiguous.

### Rule: Coalesce contiguous reads with a batch load and `extract_slice`

When the source rows are contiguous but the destinations are scattered, load
a whole contiguous block into UB once. Extract each row from UB — a cheap
local operation — and store it to its scattered location:

The two sketches below assume row-major storage, complete row and feature
tiles, in-range indices, and uniquely owned destinations. Retain masks or a
separate tail path when those facts do not hold. Each program's index loads
must use the same global row base as its data tile.

Conversely, do not leave conservative row or feature masks on the specialized
path after its wrapper contract proves complete tiles. Derive coverage from
the actual relationship, not one dimension in isolation: for example,
`top_k == 2` together with `token_rows % 16 == 0` proves
`output_rows % 32 == 0`. Under exact feature blocking as well, use unmasked
inverse loads, data loads, and data and secondary-output stores, while retaining
the original masked fallback for all other shapes. Confirm in TTIR/IR that
the hot path no longer contains boundary compares, selects, or masked
transfer operands; source-level `row_valid` that is always true can still
prevent the desired complete-tile lowering.

```python
row0 = tl.program_id(0) * BLOCK
rows = row0 + tl.arange(0, BLOCK)[:, None]
cols = tl.arange(0, D)[None, :]
data = tl.load(x_ptr + rows * D + cols)  # one contiguous tile load
for i in range(BLOCK):
    token = tl.extract_slice(data, [i, 0], [1, D], [1, 1])
    idx = tl.load(indices + row0 + i)
    tl.store(out_ptr + idx * D + cols, token)
```

### Rule: Coalesce contiguous writes with `insert_slice` and a batch store

When the destinations are contiguous but the sources are scattered, assemble
the scattered rows into a UB buffer and store the buffer once:

```python
row0 = tl.program_id(0) * BLOCK
rows = row0 + tl.arange(0, BLOCK)[:, None]
cols = tl.arange(0, D)[None, :]
buffer = tl.full((BLOCK, D), 0, dtype=x_ptr.type.element_ty)
for i in range(BLOCK):
    idx = tl.load(indices + row0 + i)
    row = tl.load(x_ptr + idx * D + cols)
    buffer = tl.insert_slice(buffer, row, [i, 0], [1, D], [1, 1])
tl.store(out_ptr + rows * D + cols, buffer)  # one contiguous tile store
```

Choose the rule by access direction: batching the wrong side leaves the
expensive scattered transfers in place.

### Rule: Batch different source and output locality axes in one local tile

Keep a small tile of logical rows live when their source order and output order
differ. For example, output rows may flatten as `b * P + p`, while a source
stream stores rows as `f(p) * B + b`. Neighboring `b` values then share one
contiguous source block, but neighboring `p` values share one output block.
Process both axes together: batch-load neighboring source rows for each
position, apply each row's original weighted combination, then reassemble
neighboring positions for each batch into a contiguous output tile. This local
reordering needs no global inverse map and writes no intermediate to memory.

For each source stream, derive indices or omit unit-weight arithmetic only
when the producer or operator contract guarantees those values for every
consumed row. Otherwise load the actual indices and weights. A small
program-uniform adjacency test can still select a regular batch load:

```python
s0 = tl.load(INDEX + route0)
s1 = tl.load(INDEX + route1)
if s1 == s0 + 1:  # both indices are valid; the whole row tile is in range
    ptr = tl.make_block_ptr(
        base=X, shape=(N_SOURCE, D), strides=(D, 1), offsets=(s0, 0),
        block_shape=(2, FEATURE_TILE), order=(1, 0),
    )
    pair = tl.load(ptr, boundary_check=(1,), padding_option="zero")
    # Extract the two rows locally; preserve their individual coefficients.
else:
    # Load each original source row separately with its exact feature mask.
    ...
```

Use a supported row extraction form such as `tl.extract_slice` or flattening
followed by `tl.gather`; assemble output-order rows with `tl.insert_slice` or
a small broadcast/select. Keep this work in UB and use [`block-pointer-tiles`](block_pointer_tiles.md)
for each proven regular transfer and [`merge-adjacent-stores`](merge_adjacent_stores.md) for output groups.
Preserve the original FMA order, accumulator dtype, and rounding points.
Partition tile ownership uniquely; handle a partial outer tile with masks or
a separate tail. Choose persistent shard count and tile size from target
measurements and live UB footprint, rather than copying a fixed launch count.

### Rule: Invert a complete permutation to own contiguous output rows

Establish the map's semantic contract from its producer: every consumed
destination is in range and appears exactly once. Shape and expansion count
alone establish only the number of routes. For a row-major expanded map, the
inverse stores source rows rather than route numbers:

```python
route = tl.program_id(0) * ROUTE_TILE + tl.arange(0, ROUTE_TILE)
valid = route < N_SOURCE * REPLICATION
destination = tl.load(FORWARD + route, mask=valid, other=0)
tl.store(INVERSE + destination, route // REPLICATION, mask=valid)
```

Use an index dtype that covers the source-row range. A separate inversion
launch provides the ordering boundary before the consumer reads the map.
Alternatively, reuse a producer-supplied inverse under the metadata and
mutation checks in [`kernel-fusion-and-value-placement`](kernel_fusion_and_value_placement.md); retain reconstruction
when that map is absent or invalid.

Launch one program per contiguous output-row tile, with the launch count
derived from the output length. Load inverse source rows, widen address
arithmetic as needed, and gather each complete feature tile into UB. A
row-local transform can run after gathering, then store both data and secondary
outputs using the output-row coordinates:

```python
out_row = tl.program_id(0) * ROW_TILE + tl.arange(0, ROW_TILE)
source = tl.load(INVERSE + out_row, mask=out_row < N_OUTPUT, other=0)
cols = tl.arange(0, FEATURE_TILE)
mask = (out_row[:, None] < N_OUTPUT) & (cols[None, :] < WIDTH)
values = tl.load(X + source.to(tl.int64)[:, None] * WIDTH + cols[None, :],
                 mask=mask, other=0)
# Apply the original row-local transform, retaining block axes and dtypes.
tl.store(Y + out_row[:, None] * WIDTH + cols[None, :], values, mask=mask)
```

For block reductions, carry a row-by-block-by-element tile and store each
block's secondary result at the same output row. Remove row or feature masks
only when dispatch proves complete tiles. Keep a contract-preserving
implementation for calls outside the complete-permutation domain.

This direction may reread and recompute a replicated source row for each
destination. Preserve the original reduction, scale arithmetic, rounding
points, and block grouping while measuring that trade. Select tile width from
the contiguous transfer direction and live UB budget; assess feature-axis
splitting with its own transfer and resource evidence.

## Avoid When

- Neither side becomes contiguous, or saved transfer cost does not repay UB
  rearrangement, adjacency branches, inversion, or duplicated transform work.
- The staged block exceeds usable UB; shrink the block before applying the
  batched form and verify allocation in generated code.
- The inverse-routing variant lacks a proven complete, in-range destination
  permutation with unique writers. Retain the contract-preserving path.
- Derived indices or omitted unit-weight arithmetic rely on observed samples
  rather than a producer or operator guarantee for every consumed row.
- Host launch overhead is the primary bottleneck; transfer batching itself
  does not coalesce repeated wrapper launches.

## What To Verify After Applying

- Verify the forward/inverse identity for every route, complete unique writes,
  in-range destinations, repeated source rows, and the correct expansion
  convention. Exercise generic inputs through the contract-preserving path.
- Compare data and secondary outputs, block grouping, reduction dtypes, scale
  guards, and staged rounding. Cover zero and near-zero blocks and numerical
  boundaries supported by the contract.
- Check complete tile coverage and tails, UB allocation, and generated source
  gather and destination store forms. Dense stores must cover both outputs.
- For a local tile, verify the source-to-output row identity, distinct and
  repeated indices, both adjacency branches, odd outer lengths, and unique
  writers at shard boundaries. Test all contributing weights and arithmetic
  rounding points. Validate any derived-index or unit-weight guarantee over
  the complete execution domain before enabling that specialization.
- Measure inversion plus gather, repeated source loads and transform work,
  allocations, and total operator latency; compare the saved transfer cost
  against the added gather, rearrangement, and branch cost. When a producer
  supplies the inverse, include both calls, confirm the separate inversion
  launch disappears on valid metadata, and exercise missing, stale, and
  unsupported metadata.

## Related Patterns

- [`kernel-fusion-and-value-placement`](kernel_fusion_and_value_placement.md): publish an inverse map as a producer byproduct across an ordered launch boundary, with mutation checks and fallback reconstruction.
- [`discrete-access-ub-staging`](discrete_access_ub_staging.md): the load-side cousin — stage the whole gather source in UB and select on-chip; this card batches the contiguous side of an index-driven movement, including scatter stores.
- [`gather-then-dense-compute`](gather_then_dense_compute.md): decouples scattered row loads from a following dense compute by staging rows into a contiguous buffer first.
- [`loop-invariant-hoisting`](loop_invariant_hoisting.md): computes block-invariant factors on compact state
  before broadcasting over the gathered data when lowering repeats them.

## Related Knowledge

- [现有知识：单位置 False 的 tl.where 退化规避](../techniques/where_optimization.md)
