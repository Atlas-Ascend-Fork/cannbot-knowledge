---
type: API
title: __float2bfloat16_rna_sat
description: 饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_ROUND模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2bfloat16_rna_sat

饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_ROUND模式，返回转换后的值。
函数原型：bfloat16_t __float2bfloat16_rna_sat(const float x)
返回值：饱和模式下将输入遵循CAST_ROUND模式转换成的bfloat16类型数据。特殊值如下：
约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。；SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float2half_rna_sat](../../half_type/half_precision_conversion_functions/_float2half_rna_sat.md)（`related`）：“__float2half_rna_sat”定义：将浮点数转换为半精度浮点数，并遵循CAST_ROUND模式，返回转换后的值。；“__float2bfloat16_rna_sat”定义：饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_ROUND模式，返回转换后的值。。实质衔接：非 sat 版本保持 float→half RNA 但不钳位；bfloat16 版本保持 RNA+sat 而改变目标格式，用于区分饱和与目标精度两项契约。
- [__float22bfloat162_rna_sat](_float22bfloat162_rna_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float2bfloat16_rna_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float2bfloat16_rna](_float2bfloat16_rna.md)（`same_topic`）：《__float2bfloat16_rna_sat》明确“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_ROUND模式，返回转换后的值。”；它与《__float2bfloat16_rna》的“遵循CAST_ROUND模式，将浮点数转换为bfloat16精度，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
