---
type: Guide
title: 矩阵乘输出的量化/反量化
description: 对于特定输入输出数据类型，Matmul支持将计算结果从L0C Buffer（CO1）搬出到Global Memory时，对输出C矩阵元素执行数据量化或反量化操作。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 矩阵乘输出的量化/反量化

## 功能介绍
对于特定输入输出数据类型，Matmul支持将计算结果从L0C Buffer（CO1）搬出到Global Memory时，对输出C矩阵元素执行数据量化或反量化操作。
-   Matmul量化场景：Matmul计算时左矩阵A、右矩阵B为half或bfloat16_t数据类型，输出C矩阵为int8_t数据类型。该场景下，C矩阵的数据从L0C Buffer（CO1）搬出到Global Memory时，会执行量化操作，将最终结果量化为int8_t类型，如下图所示。
-   Matmul反量化场景：Matmul计算时左矩阵A、右矩阵B为int8_t或int4b_t数据类型，输出C矩阵为half数据类型，或者左矩阵A、右矩阵B为int8_t数据类型，输出C矩阵为int8_t数据类型。该场景下，C矩阵的数据从L0C Buffer（CO1）搬出到Global Memory时，会执行反量化操作，将最终结果反量化为对应的half类型或int8_t类型，如下图所示。
Matmul量化/反量化包含两种模式：同一系数的量化/反量化模式、向量的量化/反量化模式，开发者在算子Tiling侧调用SetDequantType接口设置量化或反量化模式，这两种模式的具体区别为：
-   同一系数的量化/反量化模式（PER_TENSOR模式）：整个C矩阵对应一个量化参数，量化参数的shape为[1]。开发者在算子Kernel侧调用接口SetQuantScalar设置量化参数。
-   向量的量化/反量化模式（PER_CHANNEL模式）：C矩阵的shape为[m, n]，每个channel维度即C矩阵的每一列，对应一个量化参数，量化参数的shape为[n]。开发者在算子Kernel侧调用接口SetQuantVector设置量化参数。
量化/反量化模式对应的接口配置
模式：Tiling侧接口：Kernel侧接口
同一系数的量化/反量化：SetDequantType(DequantType::SCALAR)：SetQuantScalar(gmScalar)
向量的量化/反量化：SetDequantType(DequantType::TENSOR)：SetQuantVector(gmTensor)
## 使用场景
需要对矩阵计算结果进行量化/反量化操作的场景，当前该场景下，Matmul输入输出矩阵支持的数据类型如下表所示。
