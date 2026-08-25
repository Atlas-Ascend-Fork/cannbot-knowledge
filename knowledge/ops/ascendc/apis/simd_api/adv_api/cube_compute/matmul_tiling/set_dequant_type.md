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

- [矩阵乘输出的量化/反量化](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md)（`explains`）：《矩阵乘输出的量化/反量化》给出“对于特定输入输出数据类型，Matmul支持将计算结果从L0C Buffer（CO1）搬出到Global Memory时，对输出C矩阵元素执行数据量化或反量化操作。”；该约束/探针可直接复现、解释或前置验证《SetDequantType》中的“设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式”。
- [Dequantize](../../quantization/dequantize.md)（`related`）：Dequantize 与《SetDequantType》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [GetAscendDequantTmpBufferFactorSize](../../quantization/get_ascend_dequant_tmp_buffer_factor_size.md)（`related`）：GetAscendDequantTmpBufferFactorSize 与《SetDequantType》的实质衔接是：factor 查询与 GetAscendDequantMaxMinTmpSize 共同换算临时空间和单次元素数，AscendDequant 是结果消费方，SetDequantType 控制输出模式。
- [GetDequantizeMaxMinTmpSize](../../quantization/get_dequantize_max_min_tmp_size.md)（`related`）：GetDequantizeMaxMinTmpSize 与《SetDequantType》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [GetTiling](get_tiling.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetDequantType》的“设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式”在实际调用参数、数据流或结果校验上直接衔接。
- [SetCType](set_c_type.md)（`related`）：《SetCType》明确“设置C矩阵的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。”；它与《SetDequantType》的“设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
