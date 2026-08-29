---
type: API
title: SetDequantType
description: 设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetDequantType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetDequantType

该接口用于设置量化或反量化的模式。 Matmul反量化场景：在Matmul计算时，左、右矩阵的输入为int8_t或int4b_t类型，输出为half类型；或者左、右矩阵的输入为int8_t类型，输出为int8_t类型。该场景下，输出C矩阵的数据从L0C Buffer（CO1）搬出到Global Memory时，会执行反量化操作，将最终结果反量化为对应的half或int8_t类型。 Matmul量化场景：在Matmul计算时，左、右矩阵的输入为half或bfloat16_t类型，输出为int8_t类型。该场景下，输出C矩阵的数据从L0C Buffer（CO1）搬出到Global Memory时，会执行量化操作，将最终结果量化为int8_t类型。

参数：
- dequantType（输入）：设置量化或反量化时的模式。DequantType类型，该类型的定义如下方代码所示，其中参数的取值及含义如下：SCALAR：表示同一系数的量化或反量化模式。/TENSOR：表示向量的量化或反量化模式。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的量化/反量化](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md)（`explains`）：同一系数的量化/反量化：SetDequantType(DequantType::SCALAR)：SetQuantScalar(gmScalar)；SCALAR：表示同一系数的量化或反量化模式。/TENSOR：表示向量的量化或反量化模式。指南给出 Tiling 侧 SCALAR/TENSOR 与 Kernel 侧 SetQuantScalar/SetQuantVector 的配对，API 卡定义 dequantType 枚举语义和返回状态。
<!-- cannbot:related:end -->
