---
type: API
title: sqrt（数学函数）
description: 计算输入数据的平方根。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# sqrt

计算输入数据的平方根。

函数原型：template <typename T>；__aicore__ inline T sqrt(const T src)

参数：T：输入数据src的数据类型。当前支持的数据类型为float、int64_t。；src（输入）：源操作数。

返回值：输入数据的平方根。

对于数据类型为int64_t的数据，其计算结果将被截断为整数。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：输入必须为非负数。若输入为负数，则接口返回值无意义。
