---
type: Optimization
title: Intermediate UB Overflow
description: 当中间张量与输入输出合计超出 UB 时，沿一轴以 extract_slice/insert_slice 分片处理，任意时刻仅一个分片存活。
tags: [task.optimization, topic.memory, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/intermediate-ub-overflow.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Intermediate UB Overflow

## Summary

When a kernel's intermediate tensors, together with its inputs and outputs,
would exceed the Unified Buffer (UB) capacity, divide the computation into
slices along one axis and process each slice with `tl.extract_slice` and
`tl.insert_slice`, so only one slice of each tensor is live at a time.

## Use When

A kernel keeps several full-sized tensors live at once, typically in an
accumulator-style update over a whole tile:

```python
result = acc * alpha[:, None] + update  # acc, alpha, update, result all live
```

The compiler reports that the live values do not fit in UB, or the kernel
compiles only after shrinking the tile below the size the algorithm needs.
The pressure comes from the intermediate values of the computation, not
from any single input or output alone.

Processing the tile in slices keeps only one slice's intermediates live at a
time, so the same computation fits UB.

## Method

Confirm the fit first: the oversized live set must include the intermediates
you plan to slice, and slicing one axis must bring the peak live set back
under the UB limit.

The optimization core is to loop over slices along one tile axis: extract
the matching slice of every operand with `tl.extract_slice`, compute the
slice result, and write it back with `tl.insert_slice`. Peak UB usage then
scales with one slice instead of the full tile.

### Rule: Choose a slice count that divides the axis and fits UB

Pick the smallest slice count that brings one slice of every live tensor
within UB, and require it to divide the sliced axis length:

```python
num_slices = 4  # smallest count whose per-slice live set fits in UB
assert BLOCK_M % num_slices == 0
slice_size = BLOCK_M // num_slices

for i in range(num_slices):
    offset = i * slice_size
    acc_slice = tl.extract_slice(acc, (offset, 0), (slice_size, HEAD_DIM), (1, 1))
    alpha_slice = tl.extract_slice(alpha, [offset], [slice_size], [1])
    update_slice = tl.extract_slice(update, (offset, 0), (slice_size, HEAD_DIM), (1, 1))
    result_slice = acc_slice * alpha_slice[:, None] + update_slice
    acc = tl.insert_slice(acc, result_slice, (offset, 0), (slice_size, HEAD_DIM), (1, 1))
```

Treat the rewrite as a measured candidate. Inspect the generated IR to
confirm that the slice operations lower to views without an unwanted copy
and that the resulting live range and allocation really fit. If the backend
inserts a copy per slice, the extra traffic can outweigh the capacity win.
