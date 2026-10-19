---
type: Optimization
title: Algebraic optimization (pure math reformulation)
description: 用数学恒等式与保语义改写削减冗余访存遍历、全量扫描与中间量，替换为可精确补偿的等价形式。
tags: [task.optimization, topic.compute.elementwise.arithmetic, topic.compute.reduction]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/algebraic-optimization.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Algebraic optimization (pure math reformulation)

## Summary

Apply mathematical identities and semantics-preserving rewrites to reduce redundant memory passes, full data scans, contraction work, intermediates, or live ranges before micro-tuning loads. Covers floating-point identities, matrix-chain evaluation trees, operator-defined equivalences, and algebraic merge rules.

## Use When

The kernel's result is mathematically correct, but a semantics-preserving
rewrite of the math could produce the same result with less work: repeated
full passes over the same data that one fused pass could serve (e.g.
computing mean and variance in two traversals), pairwise or broadcast
expressions that factor into row/column terms (e.g. `exp(g_i - g_j)`), a
contraction chain whose parenthesization materializes an oversized
intermediate, or a loop-carried rescale dependency that a reformulation can
break. Apply these rewrites before micro-tuning tile sizes, pipelines, or
autotune grids.

## Avoid When

- The bottleneck is clearly **only** bad tile size or UB overflow with **no** redundant algorithmic passes (prefer `tile-footprint-fitting` or footprint patterns first).
- Custom Triton fusion is attempted before a simpler **host/graph reorder** is proven correct and cheaper end-to-end.
- A nonlinear operation, observable rounding boundary, bias, mask, mutation, or
  additional consumer lies between contractions and prevents reassociation.

## Signals

### Code

- Two loops or kernels with nearly identical `tl.load(x)` tiling along the same axis.
- `broadcast_tensors(x, y)` followed by elementwise truth tests on **wide dtypes** over the full broadcast shape.
- A temporary produced by one `tl.dot` is immediately consumed by another
  `tl.dot`, especially when the temporary carries a large spatial or sequence
  axis.

### Profile

- `NotEqual` / `BroadcastTo` (or equivalent ops) scale with **broadcast-expanded** `numel`, not with `numel(x) + numel(y)`.
- One contraction and the write/read of its temporary dominate total-operation
  latency even though an alternative parenthesization has a smaller analytical
  operation count.

## Related Patterns

- [compute-once-share-via-gm](./compute_once_share_via_gm.md): consider GM publication only after mathematical simplification and on-chip reuse fail to remove repeated producer work.
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md): retain the original parenthesization for
  dtype or shape regimes where floating-point reassociation misses the accuracy
  contract or performance regresses.
- [dot-operand-precision-ablation](./dot_operand_precision_ablation.md): preserve and test operand-rounding boundaries
  independently from the contraction order.
- [kernel-fusion-and-value-placement](./kernel_fusion_and_value_placement.md): compare reassociation with fusion when
  both could remove the same intermediate.
- [tile-footprint-fitting](../techniques/tiling.md): Reduce per-program working-set size through hierarchical or sub-block tiling, keeping live data within UB capacity.
- [program-multiple-rows](../techniques/tiling_and_grid_910_95.md): Amortize per-program fixed costs and improve vector-friendly batching for **row-reduction or row-wise fused kernels** by mapping **multiple rows** to one Triton `program_id` via `BLOCK_M > 1`, instead of one row per program.
- [software-pipeline](./software_pipeline.md): Inspect compiler-generated buffering and transfer-compute coordination in regular tiled loops.
- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md): hoist loop-invariant closed-form subexpressions out of a hot loop — the generic fix for repeated recomputation of the same subexpression per iteration.
- [intermediate-ub-overflow](./intermediate_ub_overflow.md)
- [autotune](../operator_optimization/autotune.md): Use Triton-Ascend autotune as the default way to search split sizes, tile sizes, and selected compile options when the kernel structure is already reasonable and the main open question is parameter choice.

## What To Verify After Applying

- Correctness vs reference: **FP order**, **NaN**, **dtype promotion**; for logical ops also **bool**, **complex**, **empty tensors**, and broadcast corners.
- Profiler: fewer passes or lower time on the merged phase for the **same** outputs.
- UB and launch: the rewrite does not force unsafe per-program working sets on NPU.
- For a contraction chain, verify both analytical operation counts and actual
  intermediate bytes, then validate every supported dtype/shape regime because
  real-number associativity does not imply floating-point equivalence.

## Principles

1. **Prove equivalence** under the operator’s reference semantics (real-number model where relevant; then **NaN**, **dtype promotion**, **complex**, **logical** truthiness as needed).
2. **Measure**: some equivalent forms have **longer dependency chains** or **higher UB peak**; algebraic “fewer ops on paper” can **regress** after lowering.
3. **Document** new catalog entries with: *when*, *signals*, *rewrite*, *why it can help on NPU*, *risks*, *verification*.

---

## Technique catalog

Each subsection is an independent pattern. Add new `### Case N` entries over time. Not every identity needs a case entry: symmetric or idempotent micro-identities (for example `min(a, b) + max(a, b)`) can cut evaluations directly — prove equivalence and measure as usual.

### Case 1: Single-pass first and second moments (mean & variance)

**When to use**

- You need **mean** and **(population) variance** (or sum of squared deviations) along a reduction axis.
- The baseline uses **two full traversals** of that axis: e.g. `sum(x)` then `sum((x - mean)**2)` or separate kernels for mean and variance.
- An explicit normalization such as `x / sqrt(eps + sum(...))` runs a reduction that could share partials with the statistics pass.

**Signals**

- Two loops (or kernels) with **nearly identical** `tl.load(x)` tiling along the same axis.
- Block-wise code re-loads the same block to apply a global statistic; an algebraic merge rule (parallel prefix, Welford merge) could let one load feed the merge.
- OPPROF: statistics phase dominated by **MTE** / **wait-on-flag**, not by vector FLOPs alone.
- Common in **LayerNorm**, **InstanceNorm**, **batch variance** along a contiguous dimension.

**Rewrite (algebra)**

For length \(n\), \(\mu = \frac{1}{n}\sum_i x_i\), population variance \(\sigma^2 = \frac{1}{n}\sum_i (x_i-\mu)^2\).

Single traversal:

- \(S_1 = \sum_i x_i\), \(S_2 = \sum_i x_i^2\)
- \(\mu = S_1/n\), \(\sigma^2 = \max(0,\, S_2/n - \mu^2)\) (clamp fixes tiny negative FP noise before `rsqrt`)

**Why it can improve performance on NPU**

- **One fewer full memory pass** over the axis for statistics; MTE and loop synchronization are often amortized.
- One `tl.load(x)` can feed **two reductions** (`sum(x)`, `sum(x*x)`).

**Risks**

- **Numerical**: \(S_2/n - \mu^2\) can be less stable than two-pass centered sums for extreme magnitudes; align with product numerics requirements.
- **UB / registers**: holding both accumulators plus `x*x` may **raise peak UB** vs. one accumulator; co-tune with **`tile-footprint-fitting`** / **`program-multiple-rows`**.
- **Alternatives**: **block-wise Welford merge** keeps a single pass but adds **merge arithmetic**; on some stacks it **does not** beat `S1+S2`—**benchmark**.

**Verification**

- Compare against reference (e.g. `torch.nn.functional.layer_norm`) on representative dtypes/shapes.
- Confirm profiler: **fewer** attributed loads or cycles in the statistics phase vs. two-pass baseline.

---

### Case 2: Truth map before broadcast for elementwise logical ops (`logical_or` / friends)

**Classification (is this “pure math”?)**

- **Yes, in the sense of this catalog**: it is a **semantics-preserving rewrite** under the **reference operator definition** (e.g. `torch.logical_or`), not a change to the intended output values.
- It is **not** a continuous real-number identity like Case 1; it is **logical / discrete** equivalence plus **broadcast algebra**: truthiness commutes with broadcasting so that per-output-index results match `logical_or(broadcast(x), broadcast(y))`.
- **Prove equivalence** under the reference (including `NaN`, `complex`, `bool`), then **measure**—fusion into custom Triton is optional and may still regress on a given NPU stack.

**When to use**

- Implementing **`torch.logical_or(x, y)`** (or similar) with **broadcasting**, where the naive pipeline does: `xb, yb = broadcast_tensors(x, y)` then **`ne` / truth tests on the full expanded numeric tensors**.
- You want fewer elementwise comparisons (and often less pressure from large temporary/broadcast paths) **before** custom Triton or mask kernels.

**Signals**

- Profiler / op statistics: **`NotEqual`** (or `Cast` around masks) scales with **broadcast-expanded** `numel`, not with `numel(x)+numel(y)`.
- Heavy **`BroadcastTo`** (or equivalent) appears **before** truth tests on wide dtypes (`fp16`/`bf16`/`fp32`).
- Shapes like `(N,1)` vs `(1,N)` or `(N,…,K)` vs `(N,1,…,1,K)` where expanded compares would touch **Θ(product of output dims)** on both operands.

**Rewrite (equivalence sketch)**

Let `T` be the reference **truth map** for one tensor (PyTorch: `logical_or` uses truthiness; for non-complex numerics, `T(a) = (a != 0)` matches `torch.ne` for the usual cases; `bool` is already boolean).

For broadcast output index `i` with preimage indices `i_x` into `x` and `i_y` into `y` (standard broadcast rules):

\[
\text{logical\_or}(x,y)[i] = T(x[i_x]) \lor T(y[i_y]) = \big(T(x) \text{ broadcast} \lor T(y) \text{ broadcast}\big)[i].
\]

Equivalent pipeline:

1. **`tx = T(x)`, `ty = T(y)`** on **original** shapes.
2. **`txb, tyb = broadcast_tensors(tx, ty)`** as **bool** (or fuse `∨` without materializing full numeric broadcast).
3. Micro-optimizations:
   - **`bool` short-circuit**: if `x.dtype is bool`, then `tx = x` (no `ne`).
   - **Empty output**: if `prod(out_shape)==0`, return `empty(out_shape, bool)` without broadcasting inputs (use `broadcast_shapes` for metadata).

**Why it can improve performance on NPU**

- **Fewer elementwise truth tests** on **expanded** floating-point buffers: compare each **stored** element of `x` and `y` once, then broadcast **bool** (narrower).
- Profiler: can shrink **`NotEqual`** / **`BroadcastTo`** when those were tied to naive ordering.

**Risks**

- **Semantics**: match reference for **`complex`** (`view_as_real` + combine real/imag), **`NaN`**, **`bool`**, and dtype rules—do not assume `!= 0` without checking each dtype.
- **Fusion is separate**: lowering to Triton may **regress** (indexing, UB, launch)—validate independently.

**Verification**

- Compare vs **`torch.logical_or(x, y)`** on dtypes/shapes (broadcast corners, empty, `NaN`, `complex` if supported).
- Profiler: reduced **`NotEqual`** / **`BroadcastTo`** before optional custom kernels.

---

### Case 3: Pairwise gated exponential factorization

**When to use**

- A causal or pairwise tile multiplies by a gate term like `exp(g_i - g_j)`.
- `g_i` and `g_j` come from the same one-dimensional time vector inside a chunk.
- The pairwise difference matrix is only used as input to `exp` and then multiplied into another tile.
- Broadcasted row/column factors can reduce live intermediates or dependency depth.

**Signals**

- Code builds `b_g_diff = b_g[:, None] - b_g[None, :]`.
- The next operation is only `b_A *= exp(b_g_diff)` or equivalent.
- The same tile already has a row-side factor, such as `beta[:, None]`, that can be merged with `exp(g_i)[:, None]`.

**Rewrite (algebra)**

For every pair `(i, j)`:

\[
\exp(g_i - g_j) = \exp(g_i) \cdot \exp(-g_j)
\]

Triton-style rewrite:

```python
# Before
b_g_diff = b_g[:, None] - b_g[None, :]
b_A *= exp(b_g_diff)

# After
b_A *= exp(b_g)[:, None] * exp(-b_g)[None, :]
```

If a row-side scale already exists, fold it into the row factor:

```python
b_A *= (b_beta * exp(b_g))[:, None] * exp(-b_g)[None, :]
```

**Why it can improve performance on NPU**

- Avoids an explicit `[BT, BT]` pairwise difference intermediate.
- Lets the compiler represent the gate as broadcasts from two `[BT]` vectors.
- Can shorten the vector dependency chain around a `tl.dot`-produced attention or recurrence tile.

**Risks**

- The factored form may evaluate two vector exponentials instead of one matrix-shaped expression; benchmark the actual lowering.
- Large positive/negative `g` values may expose different overflow/underflow timing even when the real-number identity is exact.
- If `g_i - g_j` is reused by multiple downstream expressions, keeping the explicit difference can be cheaper.
- Check NaN/inf propagation if the operator has strict edge-case semantics.

**Verification**

- Compare numerical outputs on representative gate ranges, including large magnitude values.
- Confirm profiler/IR no longer shows the targeted pairwise diff materialization or that runtime improves despite equivalent IR.
- Re-profile after adjacent layout or mask changes; this rewrite often interacts with tile live range.

---

### Case 4: Contract-gated K/V single-load reuse (value == key prefix)

**When to use**

- The operator contract guarantees `value == key[..., :Dv]` (MLA latent KV cache semantics: `Dv == Dk` or `Dv == Dk - 64`), or a similar cross-operand identity.
- The kernel loads K tiles and V tiles of the same rows in the same loop — typically once for the QK dot and again for the PV dot.

**Signals**

- Profile shows two same-row tile loads per loop trip with a large combined byte count.
- IR shows the V load re-reading bytes the K load just brought in (same base, overlapping columns).

**Rewrite**

Load each row-chunk once per trip and use it as both dot operands; drop the separate V load and the V tensor argument on the staged path entirely:

```python
# Before: per trip
kc = tl.load(k_base + rows[:, None] * sks + dk[None, :])   # for QK
v  = tl.load(v_base + rows[:, None] * svs + dv[None, :])   # same rows, prefix cols
score += tl.dot(qc, tl.trans(kc))
acc += tl.dot(p, v)

# After: per trip
kc = tl.load(k_base + rows[:, None] * sks + dk[None, :])
score += tl.dot(qc, tl.trans(kc))
acc += tl.dot(p, kc[:, :Dv])        # value == key[..., :Dv] by contract
```

When the accumulator is chunked over Dv, reuse each K chunk directly as the matching V chunk; no concat needed.

**Why it can improve performance on NPU**

- The symbolic reuse removes one matching K/V load when the contract makes the V slice identical to the K prefix; measure the actual load bytes and total-operation latency.
- The identity also halves any K_sel/V_sel workspace: gather only K, take V as its prefix view.

**Risks**

- The identity is a caller contract, not a universal truth; gate it on the operator spec or an explicit flag, never assume it for generic attention.
- Column-slice reuse (`kc[:, :Dv]`) may not lower to a free view in all Triton versions; if the slice materializes, chunk the K loads so each chunk is consumed whole.

**Verification**

- Bit-level or contract-level check that inputs satisfy the identity (the golden may state it as a caller obligation).
- Per-shape benchmark: the win is load-bound shapes; compute-bound shapes may be flat.

---

### Case 5: Precision-gated matrix-chain reassociation

Here, **order** means the parenthesization and evaluation tree of contractions
inside one operator invocation. It never means reordering, skipping, or
renumbering benchmark or accuracy-test cases.

**When to use**

- A linear contraction chain has the form `(A @ B) @ C` or `A @ (B @ C)`.
- The first result is not externally visible, mutated, shared, biased,
  normalized, masked, or otherwise transformed before the second contraction.
- One parenthesization creates a much larger intermediate or performs more
  multiply-accumulate work because one axis is substantially larger than the
  others.

**Cost model**

For `A[M,K]`, `B[K,N]`, and `C[N,P]`:

- `(A @ B) @ C` costs approximately `M*K*N + M*N*P` multiply-accumulates and
  materializes `M*N` values;
- `A @ (B @ C)` costs approximately `K*N*P + M*K*P` multiply-accumulates and
  materializes `K*P` values.

Use this model to choose a candidate, then include launch count, tile legality,
and GM traffic in the measured decision. Fewer mathematical operations do not
guarantee a faster lowering.

**What generalizes**

- The linearity proof, parenthesization cost comparison, intermediate-byte
  comparison, explicit rounding boundary, complete dtype/shape validation, and
  semantic dispatch are reusable across dense, batched, indexed, and other
  contraction chains.
- Workload-local tensor names, dimension ratios, tile sizes, measured speedups,
  and validated dispatch thresholds are evidence for that workload and target;
  do not copy them into another workload as a policy.
- A semantic shape predicate still needs a causal basis such as contraction
  cost, tile legality, or a demonstrated numerical boundary. Translating a
  benchmark case list into exact shape conjunctions is still case
  fingerprinting even when the code never reads a literal case ID.

**Implementation guidance**

1. Prove that the two contractions are adjacent and linear under the public
   operator contract.
2. Keep both `tl.dot` operand pairs in the target's native supported dtype and
   keep accumulators at the parent precision unless a separate precision
   experiment justifies a change.
3. Materialize the reassociated intermediate at an explicit dtype boundary.
   This makes the intended rounding visible and prevents an accidental global
   precision change from being attributed to reassociation.
4. Compare the complete operator, including removed and newly introduced
   intermediate traffic, not only the faster dot kernel.
5. If the complete dtype/shape matrix proves only a stable subset safe and
   profitable, dispatch on semantic dimensions and dtype. Validate adjacent or
   previously unseen shapes around each proposed boundary. Keep the original
   Triton parenthesization for every unvalidated regime; never dispatch on
   benchmark case identity or a shape tuple that merely fingerprints it.

**Risks**

- Matrix multiplication is associative over real arithmetic but not under
  finite-precision reduction and rounding. A uniform rewrite can miss strict
  matched-ratio or maximum-error contracts even with FP32 accumulators.
- A smaller intermediate can still create an unfavorable Cube shape, extra
  launch, or UB footprint.
- A framework contraction fallback may look fast but violates a pure-language
  requirement and does not validate this pattern.

**Verification**

- Run the full accuracy contract for every supported dtype, including boundary
  dimensions around each dispatch regime.
- Confirm the reassociated intermediate dtype and both dot accumulator dtypes in
  source or IR.
- Compare saved full-case artifacts against both the original implementation
  and any separately required external comparator.
- Disclose per-case regressions even when the governing geomean passes.

---

### Case 6: Fold a linear tap/group loop into pre-summed weights

**When to use**

- The hot loop iterates a fixed tap/group dimension whose terms enter the output
  **linearly**: `y = sum_g (W_g . x + b_g)`.
- The loop consumes only the same activation tile `x` and per-group weights; no
  nonlinearity, mask, or mutation sits between the groups.
- The group count multiplies the kernel's dot count and weight-read volume
  (each group re-reads its own weights per program).

**Signals**

- Profile: the kernel's time scales with the group count while the per-group dot
  shapes stay identical; weight re-read volume is `groups x` the weight size.
- Code: `for g in ...: acc += tl.dot(w[g], x)` with `w[g]` read fresh every
  program and `x` shared.

**Rewrite (algebra)**

```text
y = sum_g (W_g . x + b_g) = (sum_g W_g) . x + (sum_g b_g)
```

Fold the sum into the operator's constants once at build/cache time
(`W_sum = sum_g W_g`, `b_sum = sum_g b_g`), launch the hot kernel with the
single-group form, and cache the folded constants per shape/dtype. Only the
fp32 rounding order of the accumulated weights changes.

**Why it can improve performance on NPU**

- Removes the entire group loop from the hot kernel: fewer dots, fewer weight
  loads, shorter pipelines. The win comes from deleting the loop's dots and
  weight reads, not from speeding up individual iterations.

**Risks**

- The pre-sum changes the rounding order: validate against the operator's
  accuracy contract; storing the summed weights at activation dtype rounds the
  sum once (usually within fp16-class tolerances, but check).
- If any group term is nonlinear, masked, or has an independent consumer, the
  fold is illegal.

**Verification**

- Differential test on all cases; probe ablation of the group-loop vs folded
  kernel; check the folded constants are cached (not recomputed per call).

---

### Case 7: Break a loop-carried normalization rescale into independent passes

**When to use**

- A normalization-style loop carries an online running max with per-iteration
  rescaling (`l = l * exp(m_old - m_new) + sum(...)`), and the loop is the
  measured bottleneck while masks and exp cost little.
- Dropping the max entirely (Case 8) is
  unsafe (unbounded scores) or fails the accuracy contract.

**Signals**

- Probe ablation: removing masks or exp changes little, while splitting the
  pass changes a lot; a parallel-segment rewrite that keeps the same per-lane
  iteration count does not help (the serializer is the dependency, not the
  grid).
- IR: the `exp(m_old - m_new)` chain and accumulator rescale appear between
  iterations of the load/reduce loop.

**Rewrite**

- Replace the single online pass with independent passes: a max-only pass over
  all blocks, then a sum-of-exp pass against the fixed max, then the apply
  pass. Each block's load/reduce then pipelines across iterations.
- Pair with a block width that tracks the row extent (next power of two,
  clamped to the device's feasible maximum) so wide rows use few iterations and
  narrow rows do not waste lanes.

**Why it can improve performance on NPU**

- Removing the loop-carried scalar dependency lets the compiler overlap
  iterations; an extra read of the normalized tensor is usually absorbed by
  cache.

**Risks**

- One more full read of the input when the online pass's single read was
  intentional; verify on memory-bound shapes.
- The adaptive block width must stay within UB; a too-large block can overflow.

**Verification**

- Differential test; ablation of online vs independent passes at fixed block
  width; sweep the block width across small/mid/wide extents.

---

### Case 8: Max-free softmax (drop the running-max state)

**When to use**

- A softmax-style normalization loop over KV/tile blocks carries an online running max (`m_i`) with per-iteration rescaling (`l_i = l_i * exp(m_old - m_new) + ...`, `acc *= ...`). The rescale chain is a loop-carried dependency that serializes iterations and blocks transfer/compute overlap.

**Signals**

- A pass with only max/sum recurrence is slower than a dependency-free pass on the same tiles.
- IR shows the `exp(m_i - m_new)` chain and accumulator rescaling between iterations.

**Rewrite**

- Remove the max state only when the score range and numerical contract make `exp(s)` safe. Then accumulate `l = sum(exp(s))` and normalize at use time (`w = exp(s) * (1/l)`), using the identity `exp(s)/sum(exp(s)) == softmax(s)`.

**Why it can improve performance on NPU**

- Removing loop-carried state can let independent load, dot, and elementwise work overlap. Confirm this in the generated IR and end-to-end timing.

**Risks**

- Without the max shift, `exp(s)` can overflow or underflow. Bound both operands that produce the score and the resulting exponent range, and verify the denominator and all-masked-row behavior. If those bounds are not part of the operator contract, keep the running-max path.

**Verification**

- Compare against the running-max form on representative and boundary shapes, including extreme scores and empty rows.

**Profiler corroboration (Ascend / msprof-style):** duplicate hot `tl.load` regions, high `MOV_*` / `WAIT_FLAG` in phases that differ only by a scalar derived from the same data—the workload may be **memory- or sync-bound** and a good candidate for **fewer passes**.

---

## Relation to other patterns

| Pattern | Interaction |
|---------|-------------|
| `tile-footprint-fitting` | Algebraic rewrites often change **tile live ranges**; UB limits may force **smaller** `BLOCK_*` after fusion. |
| `program-multiple-rows` | More rows per program can **amortize** control overhead after you reduce passes—still subject to tile caps. |
| `software-pipeline` | Use **after** the math structure is stable; pipeline does not remove an **extra full scan** by itself. |
| `intermediate-ub-overflow` | If a fused algebraic path **spills UB**, stage with slices or revert a sub-expression. |
| `autotune` | Tune between **algebraic variants** with **safety bounds** on tile sizes. |

---

## Reading discipline

- Treat this file as a **living catalog**: match the operator's redundancy shape to a specific case before rewriting; do not blanket-apply one formula.
- Prefer **one** algebraic change per round, then re-profile.
- If evidence is weak, strengthen with **profiler attribution** before rewriting math.
