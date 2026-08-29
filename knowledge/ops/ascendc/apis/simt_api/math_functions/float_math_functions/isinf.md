---
type: API
title: Isinf
description: 判断浮点数是否为无穷。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Isinf

功能：判断浮点数是否为无穷。

函数原型：bool isinf(float x)

参数：x（输入）源操作数。

返回值：false：输入不是无穷；true：输入为inf、-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
