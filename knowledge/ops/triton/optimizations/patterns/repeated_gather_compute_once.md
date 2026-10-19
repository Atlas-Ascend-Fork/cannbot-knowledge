---
type: Optimization
title: Repeated Gather Compute Once
description: 当索引缓冲重复选取同一元素且下游为多重集语义时，按去重元素计算一次，再用精确代数补偿恢复多重性。
tags: [task.optimization, topic.compute.indexing, topic.compute.reduction]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/repeated-gather-compute-once.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Repeated Gather Compute Once

## Summary

When an index/pointer buffer selects the same underlying element multiple times and the downstream semantics are multiset (each occurrence counts), compute each distinct element once and restore the multiplicities with an exact algebraic compensation instead of recomputing redundant work.

## Use When

An index or pointer buffer selects elements with replacement: the same element
is gathered several times, and downstream arithmetic counts each occurrence.

```python
rows = index_row[i, :]            # values repeat, e.g. [3, 0, 3, 3, 1]
vals = gathered[rows]             # loads len(index_row) elements
out  = reduce(f(vals))            # every occurrence contributes
```

Profiling shows loads and FLOPs tracking the index buffer length while the
distinct element set is much smaller — each selected element referenced 2x
or more on average. The downstream computation must accept an exact
count-weight compensation per distinct element (softmax-family, linear sums,
moments).

Dedup to the distinct elements, compute each once, and restore the
multiplicities exactly — count weights for sums, a `log(count)` shift for
softmax.

## Avoid When

- Indices are effectively unique (dedup overhead exceeds the recompute saved).
- The downstream op is not algebraically compensable per element (e.g. order-dependent or nonlinear-in-occurrence).
- Exactness cannot be argued: the compensation must be algebraically identical (floating-point associativity aside), not approximate.

## Signals

### Code

- A gather/expand loop over an index buffer whose values repeat, feeding arithmetic that counts each occurrence.

### Profile

- Work (loads + FLOPs) proportional to `len(index_buffer)` while the distinct set is much smaller.

## Method

Confirm the fit first: the duplicate rate on the real domain justifies a
dedup pass, the downstream op is compensable per distinct element, and no
semantic branch depends on occurrence order — the semantics must be multiset
(each occurrence counts), nothing more.

The optimization core is to gather and compute each distinct element once,
then restore the multiplicities with an exact algebraic compensation: count
weights for additive terms, `log(count)` shifts inside softmax-family
exponentials.

### Rule: Shift softmax-family logits by log(count)

`c * exp(s) = exp(s + log c)`, so adding `log(count)` to each distinct logit
reproduces the multiset softmax exactly, up to floating-point reassociation:

```diff
- logits = gather(full_logits, index_row)      # one term per occurrence
- probs = tl.softmax(logits)
+ uniq, counts = dedup(index_row)              # on-device scan
+ logits = gather(full_logits, uniq) + tl.log(counts)
+ probs = tl.softmax(logits)                   # one mass per distinct group
```

Ties and masking are per-element and unaffected by multiplicity.

### Rule: Weight linear sums and moments by count

Additive reductions weight each distinct element's contribution by its
count instead of summing over occurrences:

```diff
- total = tl.sum(vals)                    # vals has one slot per occurrence
+ total = tl.sum(vals_uniq * counts)      # one slot per distinct element
```

### Rule: Publish group masses, not occurrence values

The compensated result carries one value per distinct group. Aggregate
weighted consumers use these group masses directly. A consumer that needs
per-occurrence values (per-occurrence thresholds or outputs) must divide by
`c_e` and restore the occurrence mapping first.

Discipline: measure the duplicate rate and run the dedup scan on-device
without a host sync; argue and record the compensation algebra for the
specific downstream op before keeping the rewrite.

## What To Verify After Applying

- Compensation algebra argued and recorded (softmax: log-multiplicity; linear: count weights).
- Duplicate rate on the real domain justifies the dedup scan; the scan itself is device-resident.
- Selection/threshold stages operate on group masses or explicitly divide by `c_e` before restoring occurrence-level values; masked/tie behavior per element matches the multiset semantics within tolerance.
- No semantic branch depends on occurrence ORDER (multiset semantics only).
- Re-run the `tile-footprint-fitting` search after dedup: tiles that overflowed UB on the full multiset may fit on the deduplicated set.

## Related Patterns

- [algebraic-optimization](./algebraic_optimization.md): the general exact-reassociation frame this specializes.
- [gather-then-dense-compute](../operator_optimization/device_side_gather.md): dedup shrinks the row set before densification.
- [reduction-axis-split-combine](./reduction_axis_split_combine.md): orthogonal parallelization; counts survive the split.
- [现有知识：Device-side Gather 连续化](../operator_optimization/device_side_gather.md)
