---
type: Optimization
title: Dual Vector-Core Parallel Pattern
description: 用 tl.parallel 让同一 AI Core 的两个 Vector 核同时执行任务，提高 Vector 侧并行度。
tags: [task.optimization, topic.parallelism, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/dual-vector-core-parallel.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Dual Vector-Core Parallel Pattern

## Summary

Use `tl.parallel` to run tasks in the two vector cores of an aicore at the same time.

## Use When

Two or more vector-side computations — type conversions, elementwise operations, or scaling steps — run one after another on the hot path and do not depend on each other's results. While each one runs, the second vector core of the AICore sits idle. This part of the kernel is limited by vector compute, not by memory movement.

```python
scaled_a = a.to(tl.float16) * a_s   # depends only on a
scaled_b = b.to(tl.float16) * b_s   # depends only on b
acc = tl.dot(scaled_a, scaled_b, acc)
```

Issuing the independent computations together lets both vector cores work at
once, up to halving the region's time.

## Signals

### Code

- Independent type conversions, element-wise operations, or scaling steps already exist on the hot path.
- The candidate work split is compute-side and independent, rather than shared-bandwidth memory loading.

## Avoid When

- The candidate work items still share a real data dependency.
- The operation is mostly memory loading, where shared bandwidth is already the limiting factor.
- The operation is so small that `tl.parallel` overhead is likely larger than the gain.

## Method

Confirm the fit first: the candidate branches must be compute-side and truly independent of each other — no branch may consume another branch's result — and the region must be limited by vector work rather than by shared load bandwidth.

The optimization core is to assign each independent computation to one of the AICore's two vector cores with `tl.parallel(0, 2, bind_sub_block=True)`, so the branches run at the same time instead of back to back. Keep everything after the branches, such as a `tl.dot` consumer of both results, outside the `tl.parallel` loop.

### Rule: Bind independent compute branches to separate vector cores

Split the independent computations into the `tl.parallel` branches, one per vector core:

```diff
-scaled_a = a.to(tl.float16) * a_s
-scaled_b = b.to(tl.float16) * b_s
+for core_id in tl.parallel(0, 2, bind_sub_block=True):
+    if core_id == 0:
+        scaled_a = a.to(tl.float16) * a_s   # Vector Core 0
+    else:
+        scaled_b = b.to(tl.float16) * b_s   # Vector Core 1, runs at the same time
 acc = tl.dot(scaled_a, scaled_b, acc)
```

Good branch candidates: type conversions (int8→fp32, fp32→fp16), elementwise operations such as activations or multiplies, scaling steps, and output dtype conversion with stores.

### Rule: Keep loads and tiny operations sequential

Memory loads share bandwidth between the two vector cores, so moving them into `tl.parallel` adds overhead with no concurrency gain. The same holds for operations so fast that the `tl.parallel` overhead exceeds the gain:

```python
# BAD: loads share bandwidth between the cores
for core_id in tl.parallel(0, 2, bind_sub_block=True):
    if core_id == 0:
        a = tl.load(...)   # no speedup, only overhead
```

Discipline note: apply `tl.parallel` to one region at a time and measure end-to-end latency for each change. Keep the split only if total time improves, not merely because the structure looks more parallel.

## What To Verify After Applying

- Verify the two parallel branches are actually independent and do not need cross-core ordering.
- Verify `tl.parallel` is applied to compute-side work rather than shared-bandwidth loads.
- Verify end-to-end timing improves instead of only making the structure look more parallel.
