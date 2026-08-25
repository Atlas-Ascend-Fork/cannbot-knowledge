---
type: API
title: H2Cos
description: 获取输入数据各元素的三角函数余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2cos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Cos

功能：获取输入数据各元素的三角函数余弦值。

函数原型：half2 h2cos(half2 x)

参数：x（输入）源操作数。

返回值：输入数据各元素的三角函数余弦值。本接口受全局饱和寄存器影响，。特殊值：±0→1；nan→0；±inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Cos](../../bfloat16_type/bfloat16x2_math_functions/h2cos.md)（`related`）：bfloat16x2 H2Cos 与 half2 版本均逐分量求余弦，跨 dtype 迁移时对照饱和与特殊值。
- [H2Sin](h2sin.md)（`same_topic`）：H2Sin 与《H2Cos》的实质衔接是：bfloat16x2 H2Sin执行同一双 lane 正弦，H2Cos给出配套三角函数；可直接核对 half2 特殊值与全局饱和寄存器影响。
<!-- cannbot:related:end -->
