---
type: API
title: half2类型比较函数
description: 提供half2类型数据的分量比较、最值获取与NaN判断接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/half2_compare_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half2类型比较函数

提供 half2 双分量向量类型的比较运算，涵盖相等、不等、大小关系等比较操作，每个比较提供有序（u 后缀）和无序两种语义版本，以及 _mask 掩码输出变体。还包含 NaN 判断（__isnanx2）和最值获取（__hmaxx2、__hminx2 及其 _nan 变体），支持两路并行比较。
