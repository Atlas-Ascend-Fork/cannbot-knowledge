---
type: API
title: Hexp10
description: 计算half输入x的10的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hexp10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hexp10

功能：指定输入x，获取10的x次方。

函数原型：half hexp10(half x)

参数：x（输入）源操作数。

返回值：10的x次方。本接口受全局饱和寄存器的影响，。特殊值：±0→1；inf→ASCRT_MAX_NORMAL_FP16；-inf→0；nan→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
