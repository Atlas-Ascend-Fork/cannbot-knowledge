---
type: API
title: H2Sin
description: 获取输入数据各元素的三角函数正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2sin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Sin

功能：获取输入数据各元素的三角函数正弦值。

函数原型：bfloat16x2_t h2sin(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各元素的三角函数正弦值。本接口受全局饱和模式影响，。特殊值：0→0；-0→-0；inf→0；-inf→0；nan→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Sin](../../half_type/half2_math_functions/h2sin.md)（`same_topic`）：H2Sin 与《H2Sin》的实质衔接是：bfloat16x2 H2Sin执行同一双 lane 正弦，H2Cos给出配套三角函数；可直接核对 half2 特殊值与全局饱和寄存器影响。
<!-- cannbot:related:end -->
