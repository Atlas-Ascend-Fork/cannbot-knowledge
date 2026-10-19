---
type: Optimization
title: Compiler And Lowering Hint Pattern
description: kernel 结构稳定后，用编译提示传达指针数学无法安全推断的对齐与连续性事实，仅以证据保留。
tags: [task.optimization, topic.compilation]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/compile-hint-adding.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Compiler And Lowering Hint Pattern

## Summary

Use compiler hints to communicate layout facts the compiler cannot safely infer from pointer math alone.

This is a late-stage refinement pattern: apply `tl.compile_hint(..., "dot_pad_only_k")`, `tl.multiple_of(...)`, and `tl.max_contiguous(...)` only after the main kernel structure is already strong and the remaining opportunity is in lowering.

Ascend launch options such as `multibuffer`, `set_workspace_multibuffer`, and `enable_auto_bind_sub_block` should be treated the same way: late-stage, kernel-local lowering/launch hints that require evidence. Do not copy one option set across unrelated kernels as a default.

## Use When

The kernel structure is settled, but the generated code still carries
defensive masks, padding, or narrow transfers for accesses you can prove are
aligned or contiguous: for example the compiler pads a `tl.dot` operand on
all sides even though only K needs it (M and N are already aligned), or keeps
a load/store narrow and masked even though the pointer range is provably
contiguous. Communicating the proven fact through a compiler hint lets the
lowering drop that defensive code.

## Avoid When

- The dominant issue is still structural, such as wrong tiling, launch geometry, or algorithm shape.
- Alignment or contiguity assumptions are shape-conditional and not yet guarded by dispatch.
- Hints are being used to compensate for invalid pointer or index math.
- Launch hints are being changed before algorithm, layout, and grid structure are stable.

## Signals

### Code

- `tl.dot` inputs already satisfy `M` and `N` alignment, so only the `K` direction still needs padding guidance.
- Pointer slices are known contiguous or aligned, but the code does not yet communicate that with `tl.max_contiguous` or `tl.multiple_of`.

### Profile

- The parent kernel is already strong, and hint-only rounds produce small but plausible wins.
- Some hint rounds regress despite beating historical baselines, which signals parent-vs-parent sensitivity.
- `multibuffer`, workspace multibuffer, or auto sub-block binding changes produce small mixed wins/regressions across similar kernels.

## What To Verify After Applying

- Verify the asserted alignment or contiguity assumptions are actually true for every dispatched regime.
- Verify boundary and tail behavior still works where masks and hints interact.
- Verify the hints improved lowering or performance against the immediate parent, not just against older baselines.

## Hint Rules

Apply the smallest hint set that matches the proven hot path, and scope a
hint to the dtype, shape, or dispatch branch where it is proven instead of
applying it globally.

### `dot_pad_only_k` — dot operands where only K needs padding

Use when the dot inputs' M and N extents are already aligned and only the K
direction still needs padding semantics. Effect: the compiler pads only K and
drops the M/N boundary handling for that operand.

```python
a = tl.load(a_ptrs, mask=a_mask, other=0.0)
tl.compile_hint(a, "dot_pad_only_k")   # M/N aligned; only K needs padding
b = tl.load(b_ptrs, mask=b_mask, other=0.0)
tl.compile_hint(b, "dot_pad_only_k")
acc = tl.dot(a, b, acc)
```

### `max_contiguous` — provably contiguous pointer ranges

Use when a load/store pointer range is contiguous in blocks of `N` under the
active branch contract. Effect: the compiler may emit a wider block transfer
instead of per-segment masked access. Annotate both the load source and the
store destination when both are contiguous:

```python
src = tl.max_contiguous(src_ptr, BLOCK_SIZE)  # contiguous in BLOCK_SIZE chunks
value = tl.load(src, mask=mask)
dst = tl.max_contiguous(dst_ptr, BLOCK_SIZE)
tl.store(dst, value, mask=mask)
```

### `multiple_of` — provably aligned pointers

Use when the pointer's base plus offset arithmetic provably satisfies
alignment to `N`. Effect: alignment-aware lowering (wider transfers, fewer
guards). Omit it wherever the alignment proof does not hold — a false
`multiple_of` is a correctness hazard, not just a missed optimization.

### Ascend launch hints — `multibuffer`, `set_workspace_multibuffer`, `enable_auto_bind_sub_block`

Use after the kernel structure is settled and only as a bounded A/B against
the immediate parent. Effect: changes buffer depth and sub-block binding.
Wins are per-kernel and can flip sign between sibling kernels (a forward
kernel may win with `enable_auto_bind_sub_block=True` while a gradient kernel
loses), so treat them as measured per-kernel choices, never a copied default
set:

```python
kernel[grid](..., multibuffer=True,
             set_workspace_multibuffer=2,
             enable_auto_bind_sub_block=False)
```

Include warmup so compile and autotune effects do not pollute timing, record
the exact option set in the round summary, and prefer `autotune` when several
launch or meta options interact.
