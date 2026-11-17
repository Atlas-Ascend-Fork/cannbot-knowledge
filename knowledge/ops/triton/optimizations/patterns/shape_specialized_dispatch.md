---
type: Optimization
title: Shape 特化派发
description: 按可证明的 shape 或语义守卫选择专用路径，并保留通用回退。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/shape-specialized-dispatch.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---
# Shape-Specialized Dispatch

## Summary
Use a small host-side shape discriminator to select a specialized kernel for a proven shape regime while retaining a generic fallback for all other inputs. Dispatch selects an implementation for one invocation; it does not change test-case execution order.

## Use When

You have a specialized rewrite that wins — on speed or on accuracy — only
inside a proven shape range, while the generic kernel stays correct and
competitive outside it. One of two situations:

- **Performance split**: the same kernel wins consistently on one shape
  range and regresses on another, and profile, IR, or divisibility evidence
  explains why (tails, masks, padding, occupancy, tile fit).
- **Numerics split**: an algebraic or precision rewrite that is exact in
  real-number arithmetic passes the accuracy contract only in a stable dtype
  and shape range, because reduction or rounding order changes.

In both, the boundary follows a causal property (divisibility, tile fit,
contraction cost, occupancy, or a validated numerical transition) — not the
observed benchmark case list — and is cheap to check before launch.

## Avoid When

- The divergence is within measurement noise.
- The candidate has no causal explanation or would require many overlapping branches.
- The branch would be keyed by benchmark case identity, artifact order, or
  sampled runtime values that are not constrained by the public contract.
- Exact dtype/shape conjunctions merely reproduce the benchmark case list,
  without a causal boundary or validation on adjacent and unseen shapes. This
  is case fingerprinting even if no literal case ID is read.
- The composed operator has not been correctness-tested and benchmarked end to end.

## Signals

### Code

- One kernel configuration is structurally suited to a subset of shapes.
- A candidate preserves real-number semantics but changes accumulation or
  rounding order, while the original implementation remains a valid fallback.

### Profile

- A regime-specific tail or occupancy cost dominates.

### IR

- Masks, boundary checks, or loop iteration counts change substantially by shape.

## Method

Confirm the fit first: the per-shape win/loss divergence must be stable,
larger than measurement noise, and explained by a causal shape or dtype
property. Record the complete original case set and its geomean as the fixed
baseline.

The optimization core is a host-side discriminator, evaluated before launch,
that routes inputs inside the proven regime to the specialized kernel and
everything else to the original kernel. Keep the dispatch only if regime
shapes improve, fallback shapes stay unchanged, and dispatch plus
compile/cache overhead is included in the measurement.

### Rule: Derive the boundary from a causal property

Key the predicate on the property that explains the divergence — tile
divisibility, whether a tile configuration fits, an occupancy threshold, or a
validated numerical transition:

```python
def use_specialized(m: int, n: int, k: int) -> bool:
    return k % BLOCK_K == 0 and m >= MIN_TILE_M
```

Validate the boundary on adjacent and unseen shapes. A predicate that
enumerates exact benchmark shapes reproduces the case list and is case
fingerprinting even if no case ID is read.

### Rule: Check only pre-launch properties

The discriminator reads shapes, dtypes, and alignment — values fixed before
the kernel launches. Do not key on sampled runtime values, artifact order, or
case identity.

### Rule: Keep the original kernel as the fallback

Every input outside the regime still runs the original implementation. When
the request forbids framework compute fallback, both the specialized and
generic paths stay in the permitted implementation language.

Change one thing per experiment: the discriminator and its specialized
kernel, not extra tuning knobs in the same run.

## Related Patterns

- [`algebraic-optimization`](algebraic_optimization.md)
- [`dot-operand-precision-ablation`](dot_operand_precision_ablation.md)
- [`implicit-transpose-elimination`](implicit_transpose_elimination.md)
- [`ragged-tile-early-return`](ragged_tile_early_return.md)

## What To Verify After Applying

- Specialized, fallback, boundary, and unknown shapes remain correct.
- Accuracy covers the complete dtype-by-shape matrix and both sides of every
  discriminator boundary; passing sampled case IDs is not a proof of the
  execution domain.
- The original complete case set remains the evaluation corpus; dispatch must
  not obtain its result by reordering, omitting, or renumbering cases.
- When the request forbids framework compute fallback, both specialized and
  generic paths remain in the permitted implementation language.
- The complete composed operator improves geomean without substantial regression on high-impact cases.
- Dispatch and compile/cache overhead are included in the measurement.
