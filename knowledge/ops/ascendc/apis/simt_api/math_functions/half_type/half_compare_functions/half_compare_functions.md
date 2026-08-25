---
type: API
title: half类型比较函数
description: 提供half类型数据的大小比较、最值获取与NaN/无穷判断接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/half_compare_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half类型比较函数

提供 half 类型的标量比较运算，包括相等（__heq）、不等（__hne）、大小关系（__hle、__hge、__hlt、__hgt）等比较操作，每个比较提供有序（u 后缀）和无序两种语义版本。还包含 NaN 判断（__hisnan）、无穷判断（__hisinf）和最值获取（__hmax、__hmin 及其 _nan 变体）。
