---
type: Optimization
title: Attention Visibility Mask Specialization
description: 按可见性策略（causal/window/prefix/ragged/block-sparse）对 key tile 分类，从递推域中删除不可见与完全有效的 tile。
tags: [task.optimization, topic.attention, topic.implementation.masking]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/attention-visibility-mask-specialization.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Attention Visibility Mask Specialization

## Summary

In an attention online recurrence over key tiles, use the visibility policy
(causal, window, prefix, ragged, block-sparse) to classify each key tile as
fully visible, fully invisible, or boundary for the current query tile: run
fully visible tiles mask-free, delete fully invisible tiles entirely, and
keep the semantic predicate only on boundary tiles.

## Use When

An attention kernel already runs an online recurrence over key tiles, but
loops over the full (padded or maximum) key length and rebuilds the
visibility mask on every iteration:

```python
for n0 in range(0, seq_len, BLOCK_N):   # every key tile, visible or not
    scores = tl.dot(q, tl.trans(load_k(n0)))
    scores = tl.where(visibility_mask(), scores, -inf)  # mask rebuilt every iteration
```

Visibility policies (causal, window, prefix, ragged) have regular geometric
structure, so tiles can be classified whole instead of masked element-wise:
tiles entirely inside the visible region need no mask, tiles entirely
outside can be skipped outright, and only tiles crossing the frontier keep
the mask. The loop then runs only over the visible key tiles instead of the
whole key sequence.

## Avoid When

- Visibility cannot be proven from the public attention policy and runtime metadata.
- Every key tile is partially valid, leaving no deletable region; if the call still exchanges score/probability tensors between stages, `attention-online-softmax-fusion` may apply instead.

## Signals

### Code

- The key loop always runs to a padded or maximum sequence extent.
- QK, mask construction, PV, and recurrence updates execute for tiles whose predicate is false for every element.
- One semantic mask is reconstructed on fully visible tiles.

### Profile

- Vector max, sum, exponentiation, rescaling, masking, or loop-control work grows with key-tile iteration count.
- Long shapes are vector-heavy and improve when `BLOCK_N` grows, subject to UB and numerical checks.

### IR

- Repeated predicate and `where` lowering remains inside every recurrence iteration.
- Dynamic loop splitting changes recurrence-state lowering or fails on the current compiler.

## Method

Confirm the fit first: the visibility predicate must be provable from the
public attention policy and runtime metadata, and the recurrence must
currently run to the full or padded key length. Estimate the win up front as
`ceil(visible_key_len / BLOCK_N)` versus `ceil(seq_len / BLOCK_N)` iterations
per query tile.

The optimization core is to classify each key tile of the current query tile
from the visibility policy — fully visible, fully invisible, or boundary —
then delete or unmask whole tiles instead of masking every element on every
iteration. Write the element predicate for each supported regime (causal,
global prefix, target, local window, ragged valid length) before classifying.

### Rule: Delete fully invisible tiles

A fully invisible tile still pays a load, a QK dot, a PV dot, and a
recurrence update; delete the whole iteration by bounding the loop at the
visibility frontier. For a causal policy with `BLOCK_M=BLOCK_N=128` and a
query tile covering rows `[256, 384)` (`key_position <= query_position`):

- key tiles `[0, 128)` and `[128, 256)` are fully visible for every query row;
- key tile `[256, 384)` is the partially visible diagonal boundary;
- all key tiles from 384 onward are fully invisible.

The concrete tile boundaries are:

```python
m_start = block_m * BLOCK_M
m_end = tl.minimum(m_start + BLOCK_M, seq_len)
full_end = (m_start // BLOCK_N) * BLOCK_N
frontier = m_end
```

Apply them as follows:

```diff
- for n0 in range(0, seq_len, BLOCK_N):
-     cols = n0 + tl.arange(0, BLOCK_N)
-     scores = tl.dot(q, tl.trans(load_k(n0)))
-     causal = cols[None, :] <= rows[:, None]
-     update(tl.where(causal, scores, -float("inf")), load_v(n0))
+ for n0 in range(0, full_end, BLOCK_N):
+     scores = tl.dot(q, tl.trans(load_k(n0)))
+     update(scores, load_v(n0))
+
+ if full_end < frontier:
+     cols = full_end + tl.arange(0, BLOCK_N)
+     scores = tl.dot(q, tl.trans(load_k(full_end)))
+     causal = cols[None, :] <= rows[:, None]
+     update(tl.where(causal, scores, -float("inf")), load_v(full_end))
```

The original loop takes `ceil(seq_len / BLOCK_N)` iterations. The
specialized loop takes `full_end / BLOCK_N` mask-free iterations plus one
diagonal boundary iteration. For `seq_len=1024` and this query tile, that
reduces eight recurrence iterations to three. For non-aligned
`BLOCK_M`/`BLOCK_N`, derive `full_end` from the largest key-tile boundary
visible to every row rather than copying the formula above. Keep padding
checks on the diagonal and sequence tail.

### Rule: Run fully visible tiles mask-free and keep the exact predicate only on boundary tiles

The general transformation:

```diff
- for n0 in range(0, kv_len, BLOCK_N):
-     valid = visibility(rows, cols)
-     update(mask(scores, valid))
+ frontier = visible_frontier(row_start, row_end, metadata)
+ full_end = fully_valid_tile_end(frontier, metadata, BLOCK_N)
+ for n0 in range(0, full_end, BLOCK_N):
+     update(scores_without_mask)
+ if full_end < frontier:
+     update(mask(load_boundary_scores(full_end), visibility(rows, cols)))
```

Applied to a prefix policy with `prefix_length=1025` and `BLOCK_N=128`, where
`prefix_full_end = (prefix_length // BLOCK_N) * BLOCK_N = 1024`: eight key
tiles lie fully inside the prefix and need no prefix predicate; only the tile
beginning at 1024 crosses the prefix boundary:

```diff
- for n0 in range(0, prefix_length, BLOCK_N):
-     cols = n0 + tl.arange(0, BLOCK_N)
-     visible = cols < prefix_length
-     scores = tl.dot(q, tl.trans(load_k(n0)))
-     update(tl.where(visible[None, :], scores, -float("inf")), load_v(n0))
+ for n0 in range(0, prefix_full_end, BLOCK_N):
+     scores = tl.dot(q, tl.trans(load_k(n0)))
+     update(scores, load_v(n0))
+
+ if prefix_full_end < prefix_length:
+     cols = prefix_full_end + tl.arange(0, BLOCK_N)
+     visible = cols < prefix_length
+     scores = tl.dot(q, tl.trans(load_k(prefix_full_end)))
+     update(tl.where(visible[None, :], scores, -float("inf")),
+            load_v(prefix_full_end))
```

For prefix-LM suffix rows, process globally visible prefix blocks first, then
derive the causal suffix frontier. Test aligned and unaligned prefix lengths
because an aligned prefix has no prefix-boundary tile.

### Rule: Collapse a one-iteration recurrence into direct softmax

When a constexpr guard proves the KV loop has exactly one iteration (e.g. `S_kv == BLOCK_KV`), the whole online-softmax recurrence is deletable work: no running-max chain, no correction factor, no accumulator rescale, no tail clamp. Compute direct softmax in one shot.

```diff
- acc = zeros; m_i = -inf; l_i = 0
- for n0 in range(0, S_kv, BLOCK_KV):
-     scores = dot(q, trans(load_k(n0)))
-     m_new = maximum(m_i, max(scores, 1))
-     m_safe = maximum(m_new, -80.0)
-     p = exp(scores - m_safe)
-     corr = where(l_i > 0, exp(m_i - m_safe), 0)
-     l_i = l_i * corr + sum(p, 1)
-     acc = acc * corr + dot(p, load_v(n0))
-     m_i = m_new
- out = acc / maximum(l_i, eps)
+ if S_kv == BLOCK_KV:  # constexpr: 1-iteration specialization
+     scores = dot(q, trans(load_k(0)))
+     p = exp(scores - max(scores, 1))
+     l = sum(p, 1)
+     out = dot(p, load_v(0)) / maximum(l, eps)
+ else:
+     ... original recurrence loop ...
```

Keep the branch constexpr so the compiler only emits the taken path, and keep the semantic mask, such as a causal predicate, inside the single tile.

#### Target-verified lowering notes (Ascend 950-class tightly-coupled-tile targets)

The straight-line / provably-one-iteration specialization above can **fail to
lower** on targets whose plan pass tiles every resident tile: the failure
surfaces as a bind/plan rejection (`bind-sub-block ... not tiled` or a
buffer-budget overflow) that looks like a structural wall but is not.
Target checks for making the single-shot structure lower and correct:

- Keep the loop real: pass the iteration count as a kernel argument declared
  non-specializable (for example `@triton.jit(do_not_specialize=[...])`).
  Front ends that bake integer arguments equal to 1 into compile-time
  constants collapse the loop into the straight-line body, and that body is
  what the plan stage rejects.  A loop-free body hits the same wall.
- Keep loop-carried accumulators in accumulation form (`acc = acc +
  dot(...)`).  Reassigning them (`acc = dot(...)`) deletes the carried
  dependence and re-collapses the loop into the rejected form.  With one
  iteration the extra `0 + x` add is exact.
- Keep the mask in integer arithmetic with a single floating-point cast
  after the subtract.  Folding the runtime row/sequence scalar into
  floating-point arithmetic before the compare can fail to lower on every
  tile class on such targets.

Trigger generalization: the single-shot form applies whenever a query row
block's *visible support* fits one window tile, not only when the whole key
sequence fits.  For a contiguous band with left/right widths `(wl, wr)`, a
window `[lo, lo + BAND)` with `lo = max(first_row + shift - wl, 0)` and
`BAND >= BLOCK_M + wl + wr` covers the block's entire visible range while
the key sequence stays long.  Use the unaligned `lo` base: a tile-aligned
base can miss up to `BAND - 1` columns at the top of the band.

Gate the `(operand dtype, head-dim tile, BAND)` geometry per class from
measured wins.  Wider windows multiply the resident key/value/probability
tiles and can exceed the unified-buffer budget - the plan-stage overflow
diagnostic reports the exact bit demand, which attributes the wall without
further probing.  A smaller row block also loses when a larger row block
covers the same band, because per-program prologue and load overhead
dominates; always prefer the smallest covering `BAND` and the largest row
block that fits the budget.  If a wide key tile must be loaded in a direct
transposed orientation to fit the buffer, expect a single strided gather
that can cost more than the staging it saves (see
`implicit-transpose-elimination`).

### Discipline

- Benchmark fully invisible suffix deletion before fully valid peeling; these are separate transformations even though both use the same visibility proof.
- Use `redundant-loop-work-deletion` to decide whether expressing full-valid and boundary regions as separate recurrence loops is profitable.
- Compare two bounded `BLOCK_N` values while holding `BLOCK_M`, precision, recurrence convention, and all other arithmetic fixed. Preserve a shape fallback for one-iteration or compiler-illegal regimes.
- Record deleted iterations and mask-free fully valid iterations separately by shape.

## Related Patterns

- [attention-online-softmax-fusion](./attention_online_softmax_fusion.md): if the call still exchanges score/probability tensors between QK, softmax, and PV stages, fuse into an online recurrence first.
- [redundant-loop-work-deletion](./redundant_loop_work_deletion.md): evaluate loop bounds and multi-region recurrence lowering, including tile/body coupling and the required controlled ablations.
- [exact-tile-no-boundary-fast-path](./exact_tile_no_boundary_fast_path.md): specialize boundary-only predicates after semantic visibility is preserved.
- [large-tile-fit-enabling](./large_tile_fit_enabling.md): evaluate a wider key tile together with precision or live-shape enablers.
- [attention-intermediate-vector-work-reduction](./attention_intermediate_vector_work_reduction.md): shorten the remaining serialized Cube producer -> Vector transformation -> Cube consumer path after deleting recurrence work.
- [ragged-tile-early-return](./ragged_tile_early_return.md): geometric segment-local emptiness in any ragged grid, independent of attention visibility frontiers.
- [现有知识：Attention 优化经验聚合](../experiences/attention_experiences.md)

## What To Verify After Applying

- Validate causal, prefix, target, window, and ragged regimes at aligned and unaligned frontiers, including empty and short regions.
- Check finite outputs and tolerance when `valid_k_extent <= BLOCK_N` and whenever recurrence order changes.
- Confirm fully invalid tiles perform no recurrence update and the boundary path preserves the original predicate.
- Use `redundant-loop-work-deletion` for controlled loop/body attribution when peeling creates multiple recurrence regions.
- Compare kernel and total-operation latency, recurrence iterations, peeled iterations, and deletion-versus-peeling attribution by shape.
- Record target/compiler identity and test short dynamic-loop iteration counts and repeated runs for determinism. If a target-specific compiler failure or nondeterminism is found, keep its reproducer in a decision record and retain only the general fallback rule here.
