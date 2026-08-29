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

- [__float2bfloat16_ru](_float2bfloat16_ru.md)（`same_topic`）：“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”与“遵循CAST_CEIL模式，将浮点数转换为bfloat16精度，返回转换后的值。”是双方正文中的具体合同。两端共享 float 到 bfloat16 的 CAST_CEIL 舍入合同，sat 版本增加饱和处理，互读能避免把边界值行为当成普通向上舍入。
<!-- cannbot:related:end -->
