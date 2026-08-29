---
type: API
title: is_const
description: 在程序编译时，检测一个类型是否为const限定的类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_const.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_const

在程序编译时，检测一个类型是否为const限定的类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename Tp>；struct is_const;

参数：Tp：需要检测的类型，包括基本类型（如int、float等）、复合类型（如数组、指针、引用）、用户自定义类型（如类、结构体等），以及const限定的类型本身。

返回值：is_const的静态常量成员value用于获取返回的布尔值，is_const::value取值如下：

-   true：Tp是const类型。
-   false：Tp不是const类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
