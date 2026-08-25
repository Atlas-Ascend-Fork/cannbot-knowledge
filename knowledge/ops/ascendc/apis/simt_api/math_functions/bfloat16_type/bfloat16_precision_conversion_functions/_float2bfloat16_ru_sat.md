---
type: API
title: __float2bfloat16_ru_sat
description: 饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16_ru_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2bfloat16_ru_sat

饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。
函数原型：bfloat16_t __float2bfloat16_ru_sat(const float x)
返回值：饱和模式下将输入遵循CAST_CEIL模式转换成的bfloat16类型数据。特殊值如下：
约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。；SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Bfloat16](../../../../simd_api/c_api/reg/data_type_convert/asc_float2bfloat16.md)（`related`）：《AscFloat2Bfloat16》明确“根据mask将src中的float类型数据转换为bfloat16_t类型，支持多种舍入模式与饱和模式，结果写入dst，位宽比为2:1。”；它与《__float2bfloat16_ru_sat》的“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float2bfloat16_rn_sat](_float2bfloat16_rn_sat.md)（`related`）：《__float2bfloat16_rn_sat》明确“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_RINT模式，返回转换后的值。”；它与《__float2bfloat16_ru_sat》的“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float2bfloat16_ru](_float2bfloat16_ru.md)（`same_topic`）：《__float2bfloat16_ru》明确“遵循CAST_CEIL模式，将浮点数转换为bfloat16精度，返回转换后的值。”；它与《__float2bfloat16_ru_sat》的“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
