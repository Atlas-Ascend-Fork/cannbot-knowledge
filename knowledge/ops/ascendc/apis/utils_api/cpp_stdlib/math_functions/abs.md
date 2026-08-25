---
type: API
title: abs（数学函数）
description: 获取输入数据的绝对值。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/abs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# abs

获取输入数据的绝对值。

函数原型：template <typename T>；__aicore__ inline T abs(const T src)

参数：T：输入数据src的数据类型。当前支持的数据类型为int8_t、int16_t、int32_t、float、int64_t。；src（输入）：源操作数。

返回值：输入数据的绝对值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
