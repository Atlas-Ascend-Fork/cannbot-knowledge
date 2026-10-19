---
type: Optimization
title: Direct Strided-Layout Reduction Pattern
description: 非末维单轴归约避免先做 movedim+contiguous 布局拷贝，对连续输入直接按步长访存归约。
tags: [task.optimization, topic.compute.reduction, topic.data_movement.layout_transform]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/strided-layout-reduction.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Direct Strided-Layout Reduction Pattern

## Summary

Avoid implementing a non-last-dimension single-axis reduction by first doing `movedim(...).contiguous()` or an equivalent layout copy. For contiguous row-major input, compute `[outer, reduce, inner]` from the original shape and reduce directly from the original layout with a strided/tiled kernel.

The goal is end-to-end latency, not making the new kernel faster than a pure contiguous last-dim reduction in isolation. This pattern wins when removing the copy saves more than the extra strided-access cost.

## Use When

The operator reduces one non-last axis of a contiguous row-major tensor, such as `torch.sum(x, dim=1)` on `[B, M, N]`. The current implementation first writes a transposed copy to memory so the reduction can run on the last axis:

```python
x = x.movedim(dim, -1).contiguous()   # or transpose/permute(...).contiguous()
out = sum_lastdim_kernel(x.reshape(-1, x.shape[-1]))
```

Profiling shows a `Transpose`, `Memcpy`, `DataCopy`, or `Contiguous` step before the reduction kernel. The copy takes time comparable to or larger than
the reduction kernel itself. The suffix after the reduced axis is long enough
that loads along `inner` stay reasonably coalesced.

Reducing along the strided axis directly skips the transposed copy, so the
kernel pays only for the reduction itself.

## Avoid When

- The reduction dimension is already the last dimension.
- The reduction is a full-tensor reduction such as `dim=None`; use a flat parallel reduction instead.
- The input is not contiguous and the kernel does not explicitly handle real tensor strides.
- The reduction spans multiple axes. A generalized variant may cover adjacent reduced axes that form one contiguous block, but this card assumes exactly one logical reduced axis.
- The tensor is tiny and copy cost is negligible.
- `inner_size` is very small, so coalescing is poor. For example, reducing `dim=1` on `[B, M, 1]` gives `inner_size=1`.
- The backend cannot lower the needed strided or block-pointer loads efficiently.

## Method

Confirm the fit first: the profile must show the layout copy serialized before the reduction kernel, and the lowered IR should show a temporary buffer or copy step (such as `memref.alloc`, `memref.copy`, or `DataCopy`) feeding the reduction. Record copy time and reduction-kernel time as the baseline to beat.

The optimization core is to delete the transposed copy and compute the reduction from the original layout using explicit strides, launching over `[outer, inner]` and looping over `reduce`.

### Rule: Compute `[outer, reduce, inner]` from the original shape and index it directly

For `x.shape = [B, M, N]` and `torch.sum(x, dim=1)`:

```diff
- x2 = x.movedim(1, -1).contiguous()          # [B, N, M] copy written to memory
- out = sum_lastdim_kernel(x2.reshape(-1, M))
- out = out.reshape(B, N)
+ outer_size, reduce_size, inner_size = B, M, N
+ out_2d = torch.empty((outer_size, inner_size), device=x.device, dtype=x.dtype)
+ sum_nonlastdim_kernel(x, out_2d, reduce_size=reduce_size, inner_size=inner_size)
+ out = out_2d.reshape(B, N)
```

In general, `outer_size = prod(shape[:dim])`, `reduce_size = shape[dim]`, and `inner_size = prod(shape[dim + 1:])`. For contiguous row-major input the logical address rule is:

```text
x[o, r, i] = base + o * reduce * inner + r * inner + i
```

so the logical strides are `outer = reduce * inner`, `reduce = inner`, `inner = 1`. The flattened `[outer, inner]` output is naturally contiguous and reshapes to the framework output shape without another copy.

### Rule: Launch a 2D grid over `[outer, inner]` and loop over `reduce`

A simple implementation uses one program per `outer` index and `inner` tile. A more optimized variant tiles both `outer` and `inner`. Loads come from the original tensor with explicit strides, and results are written directly to the `[outer, inner]` output.

If you use a block pointer for tile layout `[TILE_REDUCE, TILE_INNER]`, use `shape = (reduce_size, inner_size)`, `strides = (inner_size, 1)`, `block_shape = (TILE_REDUCE, TILE_INNER)`, `order = (1, 0)`, and reduce over axis 0. `TILE_REDUCE` and `TILE_INNER` are chosen by the implementation or autotuning; keep them small enough to avoid UB pressure.

### Rule: Split a very large reduction axis

If `reduce_size` is very large, a split-reduction design may beat one program looping across the full reduction axis.

Change one thing at a time and keep the rewrite only if the copy disappears from the profile and end-to-end operator time improves; strided access alone can be slower than the contiguous kernel it replaces.

## Risks

- Do not use `movedim(...).reshape(...)` as a "check"; the copy may already have happened.
- Small `inner_size` can erase the coalescing benefit even if the copy disappears.
- Large tiles can create UB pressure.
- Non-contiguous inputs need a separate stride-aware kernel.
- Floating-point differences are expected because the summation order changes.
- For `fp16` / `bf16` inputs, accumulate in `fp32` when possible before casting back to the output dtype.

## What To Verify After Applying

1. The optimized path is used only for non-last-dim reduction.
2. Input-contiguous preconditions are enforced, or real tensor strides are handled explicitly.
3. Output shape matches the framework reference for both `keepdim=True` and `keepdim=False`.
4. Profiles no longer show the pre-reduction transpose/copy path.
5. End-to-end operator time decreases, not just kernel self time.
6. Numerical differences stay within dtype-appropriate tolerance.
7. Empty reduced dimensions return zeros with the correct output shape.

## Related Patterns

- [implicit-transpose-elimination](./implicit_transpose_elimination.md): Eliminate implicit transpose-style access on Ascend NPU by ensuring operands are in the physical layout the kernel needs, avoiding compiler-injected layout transforms.
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [software-pipeline](./software_pipeline.md): Inspect compiler-generated buffering and transfer-compute coordination in regular tiled loops.
- [autotune](../operator_optimization/autotune.md): Use Triton-Ascend autotune as the default way to search split sizes, tile sizes, and selected compile options when the kernel structure is already reasonable and the main open question is parameter choice.
