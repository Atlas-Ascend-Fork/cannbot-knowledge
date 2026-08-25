---
type: API
title: Hsqrt
description: 计算half输入数据x的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hsqrt

功能：获取输入数据x的平方根。

函数原型：half hsqrt(half x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的平方根。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Sqrt](../half2_math_functions/h2sqrt.md)（`related`）：两卡都计算 half 平方根，分别处理 half2 两 lane 与 half 标量；数据是否可成对处理决定接口选择。
- [Hrsqrt](hrsqrt.md)（`related`）：Hrsqrt 计算 1/sqrt(x)，与 Hsqrt 共享非负输入域但输出语义增加倒数；两者常用于在精度与后续除法链之间选型。
- [Hsqrt](../../bfloat16_type/bfloat16_math_functions/hsqrt.md)（`related`）：bfloat16 Hsqrt 提供相同平方根语义的另一 16 位格式，可用于核对 half 与 bfloat16 的饱和/特殊值差异。
<!-- cannbot:related:end -->
