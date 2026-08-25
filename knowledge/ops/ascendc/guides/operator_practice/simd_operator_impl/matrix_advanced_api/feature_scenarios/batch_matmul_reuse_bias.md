---
type: Guide
title: Batch Matmul复用Bias矩阵
description: Batch Matmul场景中各Batch使用相同Bias时，设置isBiasBatch为false复用单个不带Batch轴的Bias矩阵。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_reuse_bias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Batch Matmul复用Bias矩阵

## 功能介绍
在Batch Matmul场景中，Matmul API可以一次性计算出多个大小为singleCoreM * singleCoreN的C矩阵。当Batch Matmul场景有Bias输入时，默认的Bias输入矩阵包含Batch轴，即Bias的大小为Batch * N。通过开启Bias复用功能，当每个Batch计算使用的Bias数据相同时，只需输入一个不带Batch轴的Bias矩阵。Batch Matmul的Bias矩阵复用功能默认不启用，用户需要设置MatmulConfig中的isBiasBatch参数为false来开启此功能。
如上图所示，Batch Matmul中未复用Bias矩阵的场景，每计算出一个singleCoreM * singleCoreN大小的C矩阵，都会与1 * singleCoreN大小的Bias矩阵相加。若不同Batch的计算使用的Bias数据相同，则多Batch计算可以复用同一个Bias矩阵，如下图所示，此场景中调用SetBias接口时，只需设置一个1 * singleCoreN大小的Bias矩阵。
## 使用场景
Batch Matmul中每个Batch的Matmul计算可以使用相同的Bias矩阵。
## 约束说明
A、B、C矩阵的Layout类型都为NORMAL时，不支持batchMode参数设为SINGLE_LARGE_THAN_L1，即Bias复用场景下，单Batch的A、B矩阵数据总和不得超过L1 Buffer的大小。

<!-- cannbot:related:start -->
## 相关

- [SetBias](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_bias.md)（`explains`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；Batch Matmul复用Bias矩阵正文说明“Batch Matmul场景中各Batch使用相同Bias时，设置isBiasBatch为false复用单个不带Batch轴的Bias矩阵”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
- [Batch Matmul基础功能](batch_matmul_basics.md)（`related`）：Bias 复用建立在 Batch Matmul 基本 shape/batch 配置上，只在各 batch 使用同一 Bias 时将 isBiasBatch 设 false。
<!-- cannbot:related:end -->
