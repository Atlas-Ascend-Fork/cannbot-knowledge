---
type: Guide
title: 矩阵向量乘
description: M=1的矩阵乘场景，通过配置A矩阵数据格式为VECTOR开启GEMV模式，减少搬运数据量提升性能。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵向量乘

## 功能介绍
矩阵向量乘（General Matrix-Vector multiplication），即GEMV，是指Matmul计算中M=1，形状为(1, K)的左矩阵A与形状为(K, N)的右矩阵B进行矩阵乘运算的场景。Matmul支持在Tiling侧与Kernel侧通过配置A矩阵的数据格式为VECTOR来开启GEMV模式，从而高效处理M=1的计算场景。若在M=1时未开启GEMV模式，Matmul计算则将M方向作为非对齐场景进行处理。GEMV模式相较于非对齐处理方式，搬运数据量更少，性能更好。
以M=1，K=256，N=32，左右矩阵数据类型为half的Matmul为具体示例，说明GEMV模式的Matmul API内部处理过程。
-   GEMV模式
将A矩阵从L1 Buffer（A1）搬运到L0A Buffer（A2）时，1*256的向量被当作16*16的矩阵进行处理，调用LoadData接口一次完成16*16分形大小的矩阵搬运。B矩阵的搬运以及矩阵乘计算跟基础场景相同，如下图所示。
-   非GEMV模式
将A矩阵从L1 Buffer（A1）搬运到L0A Buffer（A2）时，1*256的向量被当作非对齐矩阵数据进行处理，将M方向对齐到32字节后进行搬运。调用LoadData接口每次搬运16*16分形大小的矩阵，一共搬运K/16=16次，导致搬运数据量增加，性能相较于GEMV模式差，如下图所示。
## 使用场景
形状为(1, K)的A矩阵（M=1，K>1）做矩阵乘计算，即输入A矩阵的数据是向量数据。
## 约束说明
-   在Matmul计算中，若要开启GEMV模式，A矩阵的原始输入形状M必须等于1。
-   GEMV场景下，左矩阵A不支持转置。
-   GEMV场景下，Global Memory上的左矩阵数据需要保证16字节对齐。
-   MxMatmul场景计算矩阵向量乘时，左矩阵A和左量化系数矩阵scaleA仅支持内存逻辑位置为TPosition::GM。

<!-- cannbot:related:start -->
## 相关

- [AscL13dFmatrixConfig](../../../../../apis/simd_api/c_api/struct/asc_l13d_fmatrix_config.md)（`explains`）：矩阵向量乘 与《AscL13dFmatrixConfig》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [Cube计算(ISASI)GEMV](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_key_features/gemv.md)（`explains`）：矩阵向量乘 与《Cube计算(ISASI)GEMV》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [SetFmatrix](../../../../../apis/simd_api/basic_api/cube_compute/cube_load_aux_config/set_fmatrix.md)（`explains`）：矩阵向量乘 与《SetFmatrix》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [SetFmatrixBitMode](../../../../../apis/simd_api/basic_api/cube_compute/cube_load_aux_config/set_fmatrix_bit_mode.md)（`explains`）：矩阵向量乘 与《SetFmatrixBitMode》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [基础APIGEMV](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`explains`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《矩阵向量乘》明确提供“M=1的矩阵乘场景，通过配置A矩阵数据格式为VECTOR开启GEMV模式，减少搬运数据量提升性能。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Matmul特性介绍](matmul_features.md)（`same_topic`）：矩阵向量乘 与《Matmul特性介绍》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [MxMatmul场景](mx_matmul_scenario.md)（`same_topic`）：矩阵向量乘 与《MxMatmul场景》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
<!-- cannbot:related:end -->
