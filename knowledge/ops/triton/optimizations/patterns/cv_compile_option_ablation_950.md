---
type: Optimization
title: Ascend 950 CV Compile-Option Ablation And Scheduling Controls
description: Ascend 950 编译链上独立消融 Cube/Vector 流水、HFusion 向量化、多缓冲深度与 UB 块参数等调度控制项。
tags: [task.optimization, topic.compilation, topic.implementation.pipeline]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/cv-compile-option-ablation-950.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: ['950']
---
# Ascend 950 CV Compile-Option Ablation And Scheduling Controls

## Summary

The Ascend 950 Triton compilation path exposes controls that change Cube/Vector pipelining, HFusion vectorization, multi-buffer depth, and UB block planning. Treat these Ascend 950-only controls as version-qualified, independently ablatable scheduling transformations whose benefit depends on generated dataflow and on-chip resource pressure, rather than as universally beneficial performance flags.

## Use When

The target is Ascend 950, the kernel mixes Cube and Vector work — typically a
repeated Cube→Vector→Cube or load/compute/store chain, as in attention-style
kernels — and profiling suggests the two engines are waiting on each other:
pipeline stalls, cross-core wait, or buffer-reuse pressure. The kernel's
source-level structure is already settled, so the remaining headroom is in
how the compiler pipelines and buffers the dataflow. Kernels on this compile
path either set the `enable_dynamic_cv_pipeline` compile option or show
`ssbuffer` regions in the generated IR.

## Target Scope

These options are limited to the Ascend 950 (`910_95`) compile path in the inspected Triton Ascend 3.2.2 implementation. The A3 compile path does not run the same DynamicCVPipeline route or forward this option family to the same downstream pipeline, so treat the options as ineffective on A3 rather than as portable Ascend tuning controls. Re-check the compiler source before applying this statement to another release.

## Avoid When

- The target is A3 or any non-Ascend 950 architecture; these options are not effective through the inspected A3 compilation path.
- The kernel does not enter the relevant DynamicCVPipeline/HFusion/HIVM passes.
- The option is assumed to help without confirming that its module attribute or compiler flag is consumed.
- A structural option has not passed differential correctness against the original reference.
- Several options, tile sizes, layouts, and numerical changes are changed together before a matched control exists.

## Signals

### Code

- The launch carries compile metadata for multi-buffer depth or CV/HFusion behavior.
- The kernel has producer/consumer regions, `if`/multi-region control flow, or multiple Vector users of one producer.
- The kernel contains a long repeated Cube/Vector pipeline where buffer depth can affect overlap.

### Profile

- Increasing cross-core buffering helps only large shapes or reduces synchronization/wait time.
- A wider multi-buffer policy increases UB/L1/L0C pressure or makes latency worse.
- Refinement options change latency together with output differences or operation ordering.

### IR

- Module attributes such as `ssbuffer.intra_buf_count`, `ssbuffer.inter_core_buf_count`, `ssbuffer.insertionOptimization`, or `ssbuffer.enable_ub_refine_opt` are present before the consuming pass.
- NPUIR shows changed buffer counts, producer/consumer insertion points, block grouping, vector-block planning, or HFusion multi-consumer groups.
- The option is accepted by the frontend but no downstream IR/resource change appears; classify it as ineffective for that kernel/version.

## Option Semantics

### `limit_auto_multi_buffer_buffer`

Controls which local-buffer groups in a mixed Cube/Vector function may receive automatic multi-buffer marking. `"no-limit"` permits both Cube-side buffers such as L1/L0C paths and Vector-side UB load/store buffers; narrower strategies can restrict marking to one engine group. A wider policy may improve overlap, but can also increase UB/L1/L0C live storage and change memory-planning legality.

### `hfusion_enable_multiple_consumer_fusion`

Allows HFusion AutoVectorizeV2 to fuse a producer with multiple compatible Vector consumers. It is relevant to fan-out dataflow that would otherwise preserve separate consumer groups; it does not directly pipeline Cube operations and has no expected benefit when the lowered HFusion graph has no compatible multi-consumer producer.

### `intra_cache_num`

Sets the DynamicCVPipeline intra-core buffer count. It determines how many local buffer slots are allocated for dependencies within one core and can increase overlap between producer and consumer stages. The backend default is 2 in the inspected implementation; larger values consume more on-chip memory, and values of 3 or more trigger a source-level warning that they are not generally recommended.

### `inter_cache_num`

Sets the DynamicCVPipeline inter-core dependency buffer count. A value greater than 1 enables multi-buffered cross-core handling, changes synchronization/flag planning, and may overlap cross-core producer-consumer stages. It also consumes additional buffers and synchronization resources; the inspected backend default is 1.

### `load_cache_num`

Sets the load/store buffer depth used by the DynamicCVPipeline compute-memory decoupling path. Values greater than 1 can enable multi-buffer transformation for eligible GM loads; loops with a compile-time trip count no greater than the selected depth are skipped. It should be tested separately from intra/inter dependency buffering.

### `enable_buffer_insert_optimization`

Changes where DynamicCVPipeline inserts generated producer and consumer buffer logic. Instead of inserting immediately after a producer or immediately before a consumer, it anchors the chains at the end or start of the corresponding `ssbuffer.block_id` region. This can avoid redundant or interleaved tensor work around `if` and multi-region control flow, but it is a structural scheduling transformation and therefore requires full reference correctness validation.

### `enable_ub_refine_opt`

Enables additional UB planning refinements: broadcast and small-block optimization in `UBUsageOptPass`, plus extra fuse-group extraction behavior in Vector block planning when no Cube-adjacent operation is available. It can shorten live ranges or improve block grouping, but may change operation placement and ordering; treat it as correctness-sensitive rather than as a simple UB-capacity hint.

## Controlled Ablation Protocol

1. Confirm the target is Ascend 950, then record the exact Triton Ascend, BiShengIR/CANN, chip, compile mode, and metric source.
2. Keep source algorithm, tile choices, launch grid, dtype, and benchmark cases fixed.
3. Measure a no-extra-option control.
4. Test each option or coherent group independently.
5. Test combinations only after individual variants pass reference differential correctness.
6. Compare both kernel latency and total public-call latency when the workflow reports both.
7. Repeat promising variants because buffer scheduling is sensitive to runtime variance.

The recommended initial groups are: buffer depth (`intra_cache_num`, `inter_cache_num`), multi-buffer strategy (`limit_auto_multi_buffer_buffer`), and structural lowering (`hfusion_enable_multiple_consumer_fusion`, buffer insertion, UB refinement). Do not infer that a gain from one group transfers to another.

## What To Verify After Applying

- The original reference output passes the repository's differential correctness mode, including small, boundary, and large shapes.
- The requested compiler options are emitted and consumed by the intended pass.
- Buffer counts, UB/L1/L0C usage, sync/flag behavior, and fallback status remain legal.
- TTIR, TTAdapter, and NPUIR show the intended change without compensating work, uncontrolled live-range growth, or changed observable rounding.
- Kernel and total-operation latency improve repeatedly on representative shapes.
