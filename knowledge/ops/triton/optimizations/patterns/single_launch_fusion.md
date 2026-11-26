---
type: Optimization
title: 单 Launch 融合（多 kernel 基线 → 单 launch）
description: 在已优化并验证过的多 kernel 基线上，把阶段融合为单次 device launch；覆盖阶段边界分类、跨 program 的到达与数据可见性验证、舍入点保持与 fusion tax 回退。
tags:
- task.optimization
- topic.memory
- topic.data_movement
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Extension_Ops/sync_block.md
  role: primary
created_at: '2026-11-20T00:00:00Z'
updated_at: '2026-11-21T00:00:00Z'
platforms: [a2, '950']
---
# Single-Launch Fusion Pattern

单 launch 的阶段门、交接形态谱与失败归因见 [单 kernel 单 launch 的可行性体系](../techniques/single_kernel_feasibility.md)。

## Summary

Deliver a pipeline that naturally needs several stages as **one device
launch**. Build and optimize the multi-kernel baseline first, then fuse the
stages inside one kernel and keep the multi-kernel version as the reference and
fallback. The two things that decide whether the fusion is honest are stage
ordering (whether one stage's GM output is visible to another program) and
per-stage rounding points; the third is fusion tax, which can make the single
launch slower than the fused-epilogue multi-kernel delivery.

## Use When

- The delivery contract requires one device launch (or a hard launch-count cap
  of one), while the natural implementation needs several phases.
- A multi-kernel baseline already passes accuracy and has per-case latency and
  launch-count evidence, so the fusion can be compared stage by stage.
- Stage boundaries are **row-local**: the data a phase consumes was produced by
  the same program (or can be recomputed cheaply), so no cross-program
  visibility is needed.
- Outputs that must be shared across programs are **commutative
  accumulations** (scatter-add, split-K reduction over an output buffer), which
  can be expressed with atomics instead of an ordering protocol.
- The fused phases can share one tile and multibuffer regime; the fused kernel
  does not need a different tile per phase.

## Avoid When

- A phase must read a GM buffer written by **another program**, but the
  hand-off has not been verified on the target stack. Program arrival and
  visibility of the producer's stores require separate checks.
- The per-phase accumulator cannot fit the UB budget at any usable tile; forcing
  it into one kernel only shrinks tiles and loses more than the launch saves.
- Accuracy depends on a per-stage `bf16` rounding point that cannot be
  reproduced inside the fused kernel (for example a stage that rounds a
  materialised intermediate once per chunk).
- The launch overhead being removed is not a measurable share of the runtime;
  fusing a compute-bound pipeline buys nothing and risks the two problems above.

## Signals

### Code

- Several `@triton.jit` definitions are launched back to back from the host, and
  the only consumer of an intermediate tensor is the next launch.
- An intermediate is written only to be read once by the next stage, and is
  otherwise a cast, a layout copy, or a scale of a value the next stage could
  recompute.
- Host code launches the same kernel several times with different slices to
  emulate a reduction (`for chunk in ...: kernel[...](...)`).

### Profile

- Launch overhead and inter-stage GM round trips are a material share of
  end-to-end latency, and per-stage timings show one stage dominating.
- Removing an intermediate write/read pair moves the time, confirming that the
  cost sits in the stage boundary rather than in the compute.

### IR

- The intermediate tensor exists only to carry values between stages: it is
  produced by one kernel and consumed by the next with no other reader.
- Fusion-relevant layout copies or casts appear on the boundary rather than
  inside a stage's compute.

## Method

1. **Record the baseline first.** Per-case latency, launch count, and
   intermediate peak memory for every stage; that is the comparison target and
   the fallback.
2. **Classify every stage boundary.** Row-local (the consumer's data was
   produced by the same program), recomputable (cheap enough to duplicate), or
   global (needs data from another program). Fuse the first two directly; the
   third needs a validated hand-off.
3. **Prefer a dependency-free decomposition.** Re-assign ownership so that a
   program consumes only what it produced. For the remaining cross-program outputs,
   atomic accumulation removes the ordering problem only when (a) the target buffer
   is correctly initialised before any accumulation, (b) the buffer is the terminal
   output of the launch, and (c) no program in the same launch reads it before every
   contribution has landed. Otherwise design an explicit init/complete protocol, or
   let one owner reduce private partial sums; a separate clear launch must be counted
   against the task's launch contract.
4. **Validate any remaining global hand-off.** Match the barriers to the
   participating execution units and test the actual producer store layout.
   Verify arrival and payload visibility separately before relying on the
   hand-off in a fused kernel. See [跨核数据可见性](../techniques/sync_and_barrier.md)
   and [可融合重构](../techniques/fusion_friendly_restructure.md).
5. **Keep dtype and rounding points identical to the baseline.** Each stage's
   cast and rounding site must survive the fusion, including the case where the
   reference rounds a materialised intermediate once per chunk.
6. **Compare outputs one by one.** Compare every output of the fused kernel with
   the multi-kernel baseline; a matching final tensor or a good average does not
   prove the intermediate stages.
7. **Decide delivery by the same three-branch table as the multi-output GEMM chain card.**
   If the single launch is only an optimisation target, choose by measured gain. If it is a
   hard requirement and performance is observation-only, deliver the fused kernel as long as
   every required case passes accuracy and the runtime launch contract (exactly one device
   launch per case), and report the measured speedup separately. If both the single launch
   and a performance threshold are hard requirements, failing either one means acceptance is
   not met. Fall back to the multi-kernel version only when no compliant candidate exists
   (accuracy, launch contract, or the performance hard threshold unmet) and mark the conflict
   explicitly.
   The shared decision table lives in
   [多输出 GEMM 链的融合与单 launch 化](../techniques/multi_output_gemm_chain_fusion.md).

## What To Verify After Applying

- The runtime trace shows exactly one device launch per case; count the launches actually
  executed (a separate clear/zero kernel counts) instead of inferring from the number of
  `@triton.jit` definitions in the source.
- Every output matches the multi-kernel baseline per case, at the same dtype and
  rounding points, including tail and boundary blocks.
- For each remaining cross-program boundary, record independent evidence of
  program arrival and payload visibility, including workspace reuse.
- Per-case latency of the fused version is measured against the baseline, the
  fusion tax is recorded, and the fallback path is present and runnable.
- A small-case smoke and a full-accuracy pass run before any full benchmark; a
  hung benchmark yields neither an accuracy nor a performance conclusion.

## Related Patterns

- [Kernel 融合与取值下沉](kernel_fusion_and_value_placement.md)
- [结果 Tile 布局对齐](result_tile_layout_alignment.md)
- [单 Program 多行处理](program_multiple_rows.md)
- [经 GM 共享的 compute-once](compute_once_share_via_gm.md)
