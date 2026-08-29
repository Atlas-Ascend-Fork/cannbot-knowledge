---
type: API
title: Hexp2
description: 计算half输入x的2的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hexp2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hexp2

功能：指定输入x，获取2的x次方（即2^x），适用于half精度数据类型。

函数原型：half hexp2(half x)

参数：x（输入）源操作数。

返回值：2的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
