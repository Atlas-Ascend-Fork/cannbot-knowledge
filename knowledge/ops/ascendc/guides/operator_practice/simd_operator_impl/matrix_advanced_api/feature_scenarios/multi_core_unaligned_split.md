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

- [SetTail](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tail.md)（`explains`）：调用SetTail接口重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，在处理尾块的时候按照设置的值也就是tailM/tailN/tailK进行搬运和计算。；在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。；Guide 的非对齐尾块步骤直接调用该 API 合同。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：主要的切分策略有切分K轴和不切分K轴两种；若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块。对齐切分卡定义 M/N/K 多核分块与核数配置，非对齐卡补充不能整除时用 SetTail 在 Iterate 前重设尾块大小，形成同一 Matmul 切分决策的完整分支。
<!-- cannbot:related:end -->
