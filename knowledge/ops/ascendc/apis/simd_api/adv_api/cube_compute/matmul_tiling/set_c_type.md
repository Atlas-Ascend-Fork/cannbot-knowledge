---
type: API
title: SetCType
description: 设置C矩阵的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetCType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetCType

设置C矩阵的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：C矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECIN。
- type（输入）：C矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ, CubeFormat::ND_ALIGN。
- dataType（输入）：C矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16、DataType::DT_INT8、DataType::DT_INT32、DataType::DT_FLOAT8_E4M3FN、DataType::DT_HIFLOAT8。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](../../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_with_advanced_api.md)（`explains`）：示例用 SetCType 声明输出矩阵的存储位置、格式和 dtype，使 Host 计算出的 TCubeTiling 与 Kernel 侧 C 类型保持一致。
- [SetDequantType](set_dequant_type.md)（`related`）：《SetCType》明确“设置C矩阵的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。”；它与《SetDequantType》的“设置Matmul量化或反量化模式，支持同一系数和向量两种量化反量化模式”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
