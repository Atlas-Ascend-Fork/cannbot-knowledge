---
type: API
title: Fmodf
description: 获取输入数据x除以y的余数。求余数时，商取x除以y浮点数结果的整数部分。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/fmodf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Fmodf

功能：获取输入数据x除以y的余数。求余数时，商取x除以y浮点数结果的整数部分。

函数原型：float fmodf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据x除以y的余数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
