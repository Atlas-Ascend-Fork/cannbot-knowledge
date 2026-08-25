---
type: API
title: __hcmadd
description: 将三个bfloat16x2_t输入视为复数，第一个分量为实部，第二个分量为虚部，执行复数乘加运算x*y+z。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hcmadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hcmadd

功能：将三个bfloat16x2_t输入视为复数，第一个分量为实部，第二个分量为虚部，执行复数乘加运算x*y+z。

函数原型：bfloat16x2_t __hcmadd(const bfloat16x2_t x, const bfloat16x2_t y, const bfloat16x2_t z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据视为复数，执行复数乘加运算的结果。对于输入a、b、c。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hcmadd](../../half_type/half2_arithmetic_functions/_hcmadd.md)（`related`）：half2 __hcmadd 与 bfloat16x2 __hcmadd 执行同一复数 fused multiply-add，差异是元素类型和头文件。
<!-- cannbot:related:end -->
