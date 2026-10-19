---
type: Optimization
title: Invariant Preprocessing Cache
description: 在缓存身份、失效、所有权与容量合约下，跨算子调用复用纯预处理结果。
tags: [task.optimization, topic.memory, topic.implementation.memory_management]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/invariant-preprocessing-cache.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Invariant Preprocessing Cache

## Summary

Reuse pure preprocessing results across public operator invocations under explicit contracts for cache identity, invalidation, ownership, bounded storage, and cold-versus-warm cost.

## Use When

The operator is called many times with an input that does not change across
calls — e.g. a weight, a lookup table, or a layout descriptor — and every
call rebuilds the same padded, packed, transposed, quantized, or indexed
version of it before launching the kernel. A typical example:

```python
def forward(x, weight):
    packed = quantize(weight.t().contiguous())  # rebuilt on every call
    return kernel(x, packed)
```

Profiling shows the preprocessing launches, allocations, or copies taking a
visible share of per-call latency. The prepared value must be a pure function
of the source and fixed transform options — never depending on runtime
inputs, random state, or output storage — and the caller contract must give a
way to tell when the source has changed. The same source must repeat often
enough that cache hits pay for the misses.

## Avoid When

- The source may mutate without a reliable version signal, or object/storage identity can be reused after the source dies.
- Calls normally receive fresh sources, preprocessing is cheap, or the benchmark measures mostly cold misses.
- The cached value depends on runtime inputs, masks, sequence lengths, random state, output aliases, or asynchronous scratch lifetime.
- Cache growth, duplicate device storage, synchronization, lookup overhead, or eviction cost outweighs the saved preprocessing.
- The runtime or operator contract requires each call to observe source mutation immediately and the cache cannot prove freshness.

## Signals

### Code

- A wrapper performs the same `contiguous`, `permute`, pad, pack, quantize, metadata-build, or index-map construction before every kernel launch.
- An invariant operand is converted into the same consumer-native layout on every call.
- A cache key uses only shape or a raw address and omits dtype, device, layout, transform parameters, mutation version, or lifetime ownership.

### Profile

- Preparation launches, allocations, or copies recur with identical sources and consume a material fraction of the public call.
- A warm-call experiment removes preparation cost while leaving kernel work, outputs, and device placement unchanged.
- Cache lookup or synchronization dominates small or low-reuse regimes.

## Method

Confirm the fit first: the same read-only source reaches repeated calls,
preparation cost is visible in the profile, and the caller contract exposes a
version or lifetime boundary with all transform inputs available before
lookup. Record preparation cost, expected hit rate, and storage budget as the
baseline.

The optimization core is to compute the prepared representation once per
source version and reuse it across public invocations, under explicit
contracts for cache identity, invalidation, ownership, and bounded storage.
Work through the rules below in order; add cross-invocation state only when
the cheaper moves cannot remove the repeated cost.

### Rule: Exhaust cheaper options before caching

First remove unnecessary preprocessing, or let the producer write the required
representation directly. Then hoist invariant work within one kernel or one
public invocation. Introduce a cross-invocation cache only when neither move
removes the repeated cost.

### Rule: Prove the transform is pure over an explicit dependency set

```text
prepared = transform(source values, dtype, device, shape, strides/layout,
                     transform parameters, target/compiler requirements)
```

Every input to this function must be available before lookup, and nothing
outside the set may influence the prepared value.

### Rule: Build the cache key from the full dependency set

A typical key needs source identity plus a mutation or version token, device,
dtype, logical and physical shape, layout or strides, and every transform
option:

```python
key = (id(source), version_of(source), source.dtype, source.device,
       source.shape, source.stride(), transform_options)
```

Raw storage addresses alone are unsafe because allocators can reuse them.
Retain an ownership or weak-reference strategy so no stale entry outlives the
source contract.

### Rule: Keep the cache only when a measured cost model favors it

```text
uncached = calls * preparation_cost
cached = misses * preparation_cost + calls * lookup_cost
         + synchronization_cost + eviction_cost + storage_cost
```

Report the expected hit-rate regime. Do not present warm-only latency as the
complete result when production or evaluation creates fresh sources.

Discipline: measure an uncached prepared representation first, to prove the
transform — not a changed consumer kernel — owns the gain. Test mutation,
object destruction and allocator reuse, device or dtype changes, concurrent
calls, stream ordering, and eviction before keeping the cache. Retain caching
only for reuse regimes where full-call latency and storage cost improve, and
keep an uncached path for fresh or uncacheable sources.

## Related Patterns

- [loop-invariant-hoisting](../operator_optimization/loop_invariant_hoisting.md): repeated work inside one kernel loop.
- [compute-once-share-via-gm](./compute_once_share_via_gm.md): reuse across programs within one invocation.
- [amortized-neutral-padding-layout](./amortized_neutral_padding_layout.md): the padded representation and its neutral-value semantics.
- [implicit-transpose-elimination](./implicit_transpose_elimination.md) and [intermediate-layout-copy-deletion](./intermediate_layout_copy_deletion.md): the selected physical layout.
- [common-input-projection-packing](./common_input_projection_packing.md)
- [shape-specialized-dispatch](../operator_optimization/grid_dispatch_specialization.md)

## What To Verify After Applying

- Full correctness after in-place mutation, replacement, destruction and allocator reuse, device or dtype changes, and transform-parameter changes allowed by the public contract.
- Cache entries cannot expose input-dependent values, stale outputs, invalid aliases, uninitialized padding, or buffers still in asynchronous use.
- Cache size and device-memory duplication are bounded, observable, and included in the tradeoff.
- Cold miss, steady-state hit, mixed hit-rate, concurrent-call, and eviction paths are measured with the same consumer kernel and complete public-call metric.
- The saved preparation is visible in launch/profile evidence and is not offset by lookup, synchronization, recovery copies, or a worse consumer lowering.
