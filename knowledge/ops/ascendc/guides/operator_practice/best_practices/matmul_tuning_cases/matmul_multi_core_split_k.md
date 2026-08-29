---
type: Guide
title: Matmul高阶API开启多核切K
description: 当M、N轴较小无法有效切分时，开启多核切K功能实现K轴切分，使算子多核并行执行。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启多核切K

## 案例介绍
本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启多核切K功能对算子性能的提升效果。为了实现算子在多核上并行执行，提升计算效率，需要将矩阵数据进行切分，切分后的数据块被分配到不同的核上处理。通常情况下，切分矩阵数据时仅切分M、N轴，不切分K轴。若M和N较小，切分M和N轴较困难，此时需要考虑K轴切分；开启多核切K功能后，该场景下可以对矩阵的K轴进行切分，从而使算子在多核上并行执行。由于K轴较大，在该场景下不切分K轴通常会导致单核的输入数据量过大，开启K轴切分后，切分策略能够更有效地平衡输出带宽和输入带宽。
-   开启多核切K的适用场景
-   矩阵的K轴较大，M轴和N轴相比K轴较小，可以在K轴进行切分，使算子并行执行的核数更多。
-   矩阵的M轴、N轴和K轴均较大时，可以在K轴进行切分，使切分策略更好地平衡输入和输出带宽。
-   开启多核切K的约束条件
-   开启多核切K的场景，获取C矩阵结果时仅支持输出到Global Memory。
-   开启多核切K的场景，需在Kernel侧代码中首次将C矩阵分片的结果写入Global Memory之前，先对Global Memory进行清零，在获取C矩阵分片的结果时，开启AtomicAdd累加。如果不预先清零Global Memory，可能会因为累加Global Memory中的原始无效数据而产生精度问题。
-   开启多核切K的场景，不支持Bias参与矩阵乘计算。
本案例的算子规格如下：
算子规格
当前案例使用的AI处理器共24个核，算子中开启高阶API Matmul的纯Cube模式。Tiling参数如下：
-   原始shape：M=16, N= 16, K=1024。
-   单核shape：未开启多核切K时，singleCoreM=16，singleCoreN=16，singleCoreK=1024；开启多核切K后，singleCoreM=16，singleCoreN=16，singleCoreK=512。
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据。
## 分析主要瓶颈点
-   优化前的流水图如下，由于未开启多核切K，且M和N非常小，原始矩阵数据未进行切分，所有数据在单核上进行计算。
-   优化前的Profiling数据如下，可以看到算子只在单核上执行，aic_time耗时约19.60us，其中aic_mte2_time的平均耗时约为13.72us，aic_mte2_ratio占比较高。
## 设计优化方案
开启多核切K后，矩阵的K方向数据可以进行切分。如下图所示，C矩阵中的R矩阵块，是通过A1*B1+A2*B2+A3*B3累加得到的，其中，A1*B1、A2*B2、A3*B3可在多个核上并行计算。
开启多核切K功能的方式为：在GetTiling接口前调用EnableMultiCoreSplitK接口，开启多核切K，并在Kernel实现中，对C矩阵的Global Memory地址清零后开启AtomicAdd。开启多核切K的完整样例请参考多核切K场景的算子样例。

<!-- cannbot:related:start -->
## 相关

- [EnableMultiCoreSplitK](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_multi_core_split_k.md)（`explains`）：开启多核切K功能的方式为：在GetTiling接口前调用EnableMultiCoreSplitK接口，开启多核切K，并在Kernel实现中，对C矩阵的Global Memory地址清零后开启AtomicAdd。；多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。指南给出完整 Host/Kernel 操作链，API 卡固定其中开关时序与默认行为。
<!-- cannbot:related:end -->
