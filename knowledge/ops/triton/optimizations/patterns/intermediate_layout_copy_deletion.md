---
type: Optimization
title: Avoid Intermediate Layout Copies
description: 删除仅为改变布局而分配填充的中间张量，由生产者直写目标布局或消费者以显式步长读取。
tags: [task.optimization, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/intermediate-layout-copy-deletion.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Avoid Intermediate Layout Copies

## Summary

Avoid allocating and filling a temporary tensor only to change layout — after `permute`, `transpose`, or `movedim` — when the next step immediately consumes it. Have the producer write the needed layout directly, or have the consumer use explicit strides, offsets, or block-pointer metadata. The win comes from deleting a full layout-copy pass over global memory, not from making the remaining kernel compute less data.

## Use When

The current code creates an intermediate tensor purely to change the physical layout, and the next step immediately copies it into the final output or hands it to exactly one consumer. A typical example:

```python
tmp = x.permute(0, 2, 1).contiguous()      # or transpose/movedim/clone/copy_
out.copy_(tmp.reshape(out_shape))          # second full-size pass, layout only
```

The layout change must be expressible as pure address math — axis reordering, singleton-axis insertion/removal, or another affine mapping that explicit strides, tile offsets, or `tl.make_block_ptr` can describe — and the target layout must be known at dispatch time. Profiling can confirm the extra pass is a material share of the call.

The rewrite has the producer write the needed layout directly (or the consumer read via strides), deleting the intermediate entirely — roughly one full read plus one full write of it.

## Avoid When

- The intermediate layout is reused by multiple later kernels and writing it to memory once is cheaper than repeating strided access.
- The producer's natural layout has other users that would require an equally expensive recovery copy after changing its stores.
- The transform is not a simple affine layout mapping, such as value-dependent indexing that needs a different gather/scatter strategy.
- The consumer truly requires a physical contiguous layout for a backend-specific fast path, and direct strided access is slower than the one-time layout copy.
- A producer-side consumer-native layout turns an ordinary regular epilogue into segmented masked, indirect, or strided stores that lose a direct Fixpipe/store path; compare that lowering with a regular output plus one explicit layout bridge.
- The layout copy intentionally converts a hot strided kernel access into contiguous time-axis loads, such as `[B, T, HV] -> [B, HV, T]` for repeated per-head chunk loads. In that case, treat the copy as an explicit layout optimization and verify it end-to-end instead of deleting it blindly.
- The tensor is tiny and the extra branch, specialization, or kernel complexity costs more than the removed copy.
- Non-contiguous inputs are allowed but the rewritten kernel only handles contiguous row-major strides.
- The final output has aliasing or in-place semantics that make direct writes unsafe.

## Signals

### Code

- A wrapper computes `tmp = x.permute(...).contiguous()` or `tmp = x.transpose(...).contiguous()` before launching another kernel.
- A dispatch branch squeezes a singleton dimension, calls a lower-rank helper, then performs `out.copy_(tmp.reshape(out_shape))`.
- A kernel writes an intermediate layout and a later copy writes the same number of elements to the final output.
- Flat offset code decodes output coordinates and maps them back to input strides, but only as a generic fallback for a small set of known permutations.
- A specialized tile kernel already exists for the reduced-rank or transposed case, but it writes to a temporary output instead of the final buffer.
- A producer writes a natural layout, a standalone affine transform creates a second layout, and exactly one heavy consumer reads only the transformed copy.

### Profile

- End-to-end latency includes a separate layout-copy, transpose, or copy kernel before or after the main computation.
- The layout-copy time scales with full tensor size and is comparable to the useful compute/copy kernel.
- Removing a temporary should reduce global-memory traffic by roughly one full read plus one full write of the intermediate tensor.

### IR

- Lowered IR contains a temporary allocation or copy-like phase whose shape matches a permuted or squeezed view.
- The hot path shows a layout transform followed by another full read/write pass over the same logical data.
- A regular producer store is eligible for direct Fixpipe, while the consumer-native candidate lowers through multiple destination stores, Vector staging, or per-element address/mask generation.

## Method

Confirm the fit first: the intermediate exists only for the layout change, it has exactly one real consumer besides the next copy or compute step, and the layout-copy time is comparable to the useful work. Record tensor sizes, dispatch branches, and the producer/consumer layouts as the fixed baseline.

The optimization core is to delete the layout-only global-memory pass: the producer stores the consumer-ready layout directly, or the consumer reads the producer layout through an explicit affine mapping. Keep producer and consumer as separate launches when their ownership or tile schedules are incompatible — deleting the bridge does not require computational fusion. The same boundary rewrite applies to any internal affine layout bridge with one dominant consumer (recurrence projections, grouped contractions, packed expert buffers, patchification frontends); attention projection-to-head layout is one instance, not the definition of the pattern.

Apply the rules below, keep the generic fallback for unsupported permutations, and keep the rewrite only when the profile loses the copy kernel without a slower producer epilogue.

### Rule: Pass the final output buffer to the layout-aware kernel

Do not stage a temporary that is only a bridge to the final layout:

```python
tmp = triton_permute(x_squeezed, new_dims)
out.copy_(tmp.reshape(out_shape))
```

Pass the final output to the kernel that already knows the layout:

```python
_launch_rank3_perm_201(x_squeezed, out)
```

### Rule: Choose which side of an internal boundary absorbs the layout

When a producer result crosses an affine layout-only bridge into one heavy consumer, compare both placements and keep the cheaper:

```python
# Baseline: a full GM layout bridge between compatible stages.
tmp = producer(x)
out = consumer(tmp.permute(order).contiguous())

# Candidate A: producer stores the consumer-ready physical layout.
consumer_input = producer(x, output_layout="consumer_ready")
out = consumer(consumer_input)

# Candidate B: consumer reads the producer layout through explicit strides.
tmp = producer(x)
out = consumer(tmp, input_layout="producer_native")
```

### Rule: Encode the affine mapping with strides or a block pointer

Inside the kernel, prefer a tile whose axes match one side of the transform — usually the load side for read bandwidth or the store side for write coalescing — then store to the final layout with explicit offsets or a block pointer instead of flat div/mod coordinate decoding:

```python
values = tl.load(src + src_offsets, mask=src_mask)
tl.store(dst + dst_offsets, values.permute(1, 0), mask=dst_mask)
```

For `out = x.permute(0, 2, 1)` on contiguous `[B, M, N]`, a direct 2D tile transpose per batch avoids a generic flat coordinate decoder:

```python
x_block = tl.make_block_ptr(
    base=x + b * M * N,
    shape=(M, N),
    strides=(N, 1),
    offsets=(m0, n0),
    block_shape=(BLOCK_M, BLOCK_N),
    order=(1, 0),
)
values = tl.load(x_block, boundary_check=(0, 1), padding_option="zero")

out_block = tl.make_block_ptr(
    base=out + b * M * N,
    shape=(N, M),
    strides=(M, 1),
    offsets=(n0, m0),
    block_shape=(BLOCK_N, BLOCK_M),
    order=(1, 0),
)
tl.store(out_block, tl.trans(values), boundary_check=(0, 1))
```

### Rule: Write squeezed singleton axes directly to the final output

When a singleton axis only changes shape metadata, the flattened storage order is unchanged. A lower-rank specialized kernel can then write the higher-rank final output directly (through `out.reshape(-1)` or an equivalent view) instead of producing a squeezed temporary and copying it back.

### Rule: Inspect the producer epilogue before crediting the win

A destination mapping that is affine at source level can still miss a backend fast path restricted to one regular store. If the consumer-native layout turns a regular epilogue into segmented masked, indirect, or strided stores, compare that lowering against a regular packed store plus one explicit layout bridge. Record store classes, direct Fixpipe eligibility, Vector staging, and per-destination masks before attributing a win to the deleted copy.

Discipline note: a new layout is not automatically better. Compare producer store coalescing, consumer access, extra padding, fan-out recovery, and total-operation latency, and keep the fallback path for non-contiguous, unsupported-rank, or uncommon layout cases.

## What To Verify After Applying

1. Correctness matches the original layout semantics for all dispatched shapes and permutations.
2. The optimized branch writes exactly the final output layout, not a temporary layout that merely has the same number of elements.
3. Profiles no longer show the removed `copy_`, `Transpose`, `Contiguous`, or intermediate layout-conversion kernel.
4. Total global-memory traffic decreases for the targeted branch.
5. Block-pointer `shape`, `strides`, `offsets`, `block_shape`, and `order` match the physical source and destination layouts.
6. Singleton-axis rewrites preserve flattened element order before writing directly to a reshaped final output.
7. Fallback paths still cover non-contiguous, unsupported-rank, or uncommon layout cases.
8. Producer and consumer remain independently scheduled when fusion is not part of the candidate, and no hidden recovery copy was introduced for another user.
9. Producer-kernel time did not regress: the consumer-native store did not exchange one global-memory pass for a slower segmented epilogue.

## Related Patterns

This card owns deletion of an affine layout-only global-memory bridge by changing producer stores or consumer indexing; route neighboring decisions as follows.

- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): owns launch grouping, recomputation, ownership, and retained-boundary decisions.
- [implicit-transpose-elimination](./implicit_transpose_elimination.md): owns physical GEMM operand orientation and cached prearrangement of invariant operands, avoiding compiler-injected layout transforms.
- [strided-layout-reduction](./strided_layout_reduction.md): avoid implementing a non-last-dimension single-axis reduction by first doing `movedim(...).contiguous()` or an equivalent layout copy.
- [block-pointer-tiles](../techniques/memory_access_optimization.md): use `tl.make_block_ptr` as a compiler-facing representation candidate when source semantics define a regular multidimensional tile but IR suggests that manual pointer expressions lower into unexpectedly scalarized, fragmented, strided, or transpose-heavy memory operations.
- [pad-copy-row-col-tiling](./pad_copy_row_col_tiling.md): rewrite flat 1D copy kernels over `numel(out)` into row–column tiled form to reduce scalar overhead from per-element coordinate reconstruction on the last dimension.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md): introduce and cost a neutral-padded physical representation when it amortizes boundary work across repeated consumers.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md): remove boundary-only predicates after the selected physical layout proves exact coverage.
- [common-input-projection-packing](./common_input_projection_packing.md): evaluate regular packed output, consumer-native segmented stores, and partial sibling groups when several affine projections share an input.
- [现有知识：Permute / Layout-transform 优化](../operator_optimization/permute_layout_transform.md)
