---
type: API
title: is_integral
description: 在程序编译时，检测一个类型是否为整数类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_integral.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_integral

在程序编译时，检测一个类型是否为整数类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename T>；struct is_integral;

参数：T：需要检测的类型，包括基本数据类型、修饰类型等。

返回值：is_integral的静态常量成员value用于获取返回的布尔值，is_integral::value取值如下：

-   true：Tp是数组类型。
-   false：Tp不是数组类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
