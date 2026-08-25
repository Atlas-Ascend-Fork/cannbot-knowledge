---
type: API
title: SetQuantVector
description: 对输出矩阵采用向量进行量化或反量化，对每一列采用参数向量中对应列的系数，需在Iterate前调用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetQuantVector.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetQuantVector

本接口提供对输出矩阵采用向量进行量化或反量化的功能，即对于输入shape为[1, N]的参数向量，N值为Matmul矩阵计算时M/N/K中的N值，对输出矩阵的每一列都采用该向量中对应列的系数进行量化或反量化。 Matmul反量化场景：在Matmul计算时，左、右矩阵的输入为int8_t或int4b_t类型，输出为half类型；或者左、右矩阵的输入为int8_t类型，输出为int8_t类型。该场景下，输出C矩阵的数据从L0C Buffer（CO1）搬出到Global Memory时，会执行反量化操作，将最终结果反量化为对应的half或int8_t类型。 Matmul量化场景：：在Matmul计算时，左、右矩阵的输入为half或bfloat16_t类型，输出为int8_t类型。

函数原型：
__aicore__ inline void SetQuantVector(const GlobalTensor<uint64_t>& quantTensor)
__aicore__ inline void SetQuantVector(const LocalTensor<uint64_t>& quantTensor)

参数：
- quantTensor（输入）：量化或反量化运算时的参数向量。参数向量的存储位置为GM或L1 Buffer。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的量化/反量化](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md)（`explains`）：PER_CHANNEL 模式要求 Iterate 前用 SetQuantVector 设置按 C 矩阵列索引的系数向量。
- [SetQuantScalar](set_quant_scalar.md)（`same_topic`）：SetQuantVector 为 C 矩阵提供逐行/逐通道量化参数，而 Scalar 对全矩阵只用 shape=[1] 系数，是直接选型对。
<!-- cannbot:related:end -->
