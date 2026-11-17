---
type: Optimization
title: 先 Gather 再稠密计算
description: 把选中行收集到连续缓冲区，再执行规则的 dot 或归约，避免热循环反复离散读取。
tags:
- task.optimization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/gather-then-dense-compute.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Gather Then Dense Compute

## Summary

When a kernel's hot path feeds indirect/random-row loads into regular dense arithmetic, split the work into two phases: one streaming pass that writes the referenced rows into a contiguous buffer (with any dtype conversion folded in), then a dense tiled compute (dot-matmul-rewrite) over that buffer. Adding a write-plus-read round trip can beat indirect loads when the index distribution has spread.

## Use When

Your kernel's hot loop resolves data-dependent row indices and loads scattered rows before a regular dot or reduction:

```python
for k in range(num_steps):                 # every iteration re-gathers
    row_ptr = base + idx[k] * stride       # data-dependent pointer
    vals = tl.load(row_ptr + offs)         # one random row per lane
    acc = tl.dot(vals, w, acc)             # dense math on gathered rows
```

Profiling shows the gather dominating the path: many small indirect row
loads that the compiler cannot turn into block transfers. The selected rows
are a small share of the source (topK rows, not the whole source), so
gathering them once into one contiguous buffer is cheap to stream. And the
indices are spread out — if many lanes hit the same address, even the densify
pass would serialize on those hot spots.

The rewrite gathers the selected rows once into a contiguous buffer, so the
dense compute then runs on contiguous loads at full rate instead of scattered
row loads.

## Avoid When

- The indices are effectively all identical (hot-spotting makes the densify pass slow too); compute the referenced-row set instead.
- `dense-substitution` wins instead: computing over the FULL source with a scattered mask is cheaper when the selection ratio is high and the mask matrix is affordable.
- The source working set is already cache-resident and the gather is a row-indexed, `BLOCK_D`-wide contiguous load rather than a per-element issue floor: densification then only adds a write pass plus a cold read of a larger buffer.

## Signals

### Code

- Per-lane index arithmetic (`row = base + idx[k]`) feeding `tl.load` with data-dependent pointers, followed by `tl.dot` or a reduction.
- A score/attention kernel whose K-loop is bounded by indirect loads rather than compute.

### Profile

- Kernel latency far above the contiguous-re-read floor of the referenced bytes.
- Vector lane utilization collapses inside the indirect loop while cube utilization stays near zero. The imbalance alone is not a trigger: it can also be irreducible softmax/cast/mask work, so treat it as a reason to run the complete paired candidate, never as confirmation.

## Method

Confirm the fit first: the code shows the indirect-load shape above, profiling
shows gather traffic dominating, the index distribution has spread, and the
selection ratio leaves a small streamable buffer. If any of these fails, stop
and follow Avoid When instead.

The optimization core is a two-phase split:

```python
# Phase 1 (streaming): contiguous stores, dtype conversion folded in
buf[i] = convert(src[idx[i]])

# Phase 2 (dense): classic tiled dot over the contiguous buffer
acc = tl.dot(tile_of_buf, w, acc)   # same result as the indirect form
```

Phase 2 is a standard [`dot-matmul-rewrite`](dot_matmul_rewrite.md) over `buf` and produces exactly
the same values as the indirect formulation; only the operand layout changes.

### Rule: Evaluate densification and consumer batching as one candidate

Densification makes every consumer program re-read the dense buffer and adds
a write plus a cold read. Measured alone, the complete form can be neutral or
negative unless the consumer axis is batched at the same time
([`gqa-kv-shared-row-batching`](gqa_kv_shared_row_batching.md)). Run and judge the paired form, not the densify
pass in isolation.

### Rule: Refute only with a real two-phase implementation

A same-kernel address substitution (`idx -> affine base`, or a
contiguous-row probe inside the original kernel) is NOT an A/B of this
pattern and cannot refute it. Only a real two-phase implementation, measured
end-to-end in the paired consumer form, counts as evidence either way.

## What To Verify After Applying

- Phase 1 reads are streaming (contiguous stores, conversion folded), and the buffer is consumed by dense tiles only.
- Index distribution has spread; degenerate buffers take a guarded path.
- Numerics unchanged (conversion placement is the only difference) against the indirect formulation; if a pure-fp32 MERE/matched_ratio fails at ~1 ulp after regrouping, re-sync the reference semantics first, then apply [`hilo-split-matmul`](hilo_split_matmul.md) to the fp32 probabilities.
- Decision boundary against `dense-substitution` recorded for the operator's shape regime.
- Re-run the [`tile-footprint-fitting`](tile_footprint_fitting.md) search after densification: the operand layout changes, so a tile that overflowed UB in the indirect form may now fit (or vice versa).

## Related Patterns

- [`dense-substitution-fine-grained-sparse-attention`](dense_substitution_fine_grained_sparse_attention.md): the complementary branch; one decision point, two outcomes.
- [`dot-matmul-rewrite`](dot_matmul_rewrite.md): phase 2 structure.
- [`shape-specialized-dispatch`](shape_specialized_dispatch.md): densify vs indirect may dispatch per shape regime.
- [`scattered-transfer-batching`](scattered_transfer_batching.md): batch the scattered transfers themselves via UB-staged slices when there is no dense-compute phase to separate.
