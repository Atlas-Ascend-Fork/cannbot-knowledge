---
type: Guide
title: 多核非对齐切分
description: 多核场景，对矩阵进行切分时，若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块，即多核非对齐场景。如下图矩阵A、B的最后一行和最后一列的矩阵块：
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_unaligned_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 多核非对齐切分

## 功能介绍
多核场景，对矩阵进行切分时，若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块，即多核非对齐场景。如下图矩阵A、B的最后一行和最后一列的矩阵块：
此时，C矩阵中的R矩阵块，依然是通过A1*B1+A2*B2+A3*B3+A4*B4累加得到的，处理A1*B1、A2*B2、A3*B3、A4*B4等尾块时，需在kernel侧设置尾块大小，在不改变原有tiling的情况下，调用SetTail接口重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，在处理尾块的时候按照设置的值也就是tailM/tailN/tailK进行搬运和计算。
## 使用场景
多核处理Matmul矩阵计算，存在尾块的场景。
## 约束说明
处理尾块调用的SetTail接口，需要在Iterate/IterateAll之前调用。

<!-- cannbot:related:start -->
## 相关

- [SetAlignSplit](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_align_split.md)（`explains`）：即使设置对齐值，矩阵总 M/N/K 不能整除 singleCore shape 时仍会出现尾块；指南要求在 Iterate 前用 SetTail 处理。
- [SetTail](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tail.md)（`explains`）：多核 M/N/K 不能整除 singleCoreM/N/K 时产生尾块；指南解释何时需要 SetTail/SetSingleShape 重设本次计算范围。
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../../../../../runbooks/precision/findsplitaxis_total_slots_slot.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《多核非对齐切分》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [多核非对齐 DataCopyPad 写回边界互相覆盖](../../../../../runbooks/precision/multicore_non_aligned_datacopypad_rmw_overlap.md)（`related`）：指南给出多核非对齐切分时首尾和核间边界的分配方式，直接解释如何避免相邻核共享一个 32B GM 写回块。
- [非对齐场景](../../vector_programming/unaligned_scenario.md)（`related`）：多核非对齐切分说明多核场景，对矩阵进行切分时，若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块，即多核非对齐场景。如下图矩阵A、B的最后一行和最后一列的矩阵块：；对非对齐场景而言，非对齐分块需要多核首尾边界方案；SwiGLU 在非 32B slice 的失败实例提供了对齐假设的反证与验证信号。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《多核非对齐切分》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [矩阵乘输出的N方向对齐](matmul_output_n_alignment.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《多核非对齐切分》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
<!-- cannbot:related:end -->
