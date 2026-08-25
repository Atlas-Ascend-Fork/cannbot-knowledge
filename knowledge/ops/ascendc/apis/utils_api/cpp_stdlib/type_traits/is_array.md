---
type: API
title: is_array
description: 在程序编译时，检测一个类型是否为数组类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_array.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_array

在程序编译时，检测一个类型是否为数组类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename Tp>；struct is_array;

参数：Tp：需要检测的类型，包括基本类型（如int、float等）、复合类型（如指针、引用）、用户自定义类型（如类、结构体等），以及数组类型本身。

返回值：is_array的静态常量成员value用于获取返回的布尔值，is_array::value取值如下：

-   true：Tp是数组类型。
-   false：Tp不是数组类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Conditional](conditional.md)（`related`）：is_array 与《Conditional》的衔接是：is_array 的布尔 trait 结果可直接作为 Conditional/EnableIf 的编译期条件，用于对数组类型启用或选择实现。
- [EnableIf](enable_if.md)（`related`）：is_array 与《EnableIf》的衔接是：is_array 的布尔 trait 结果可直接作为 Conditional/EnableIf 的编译期条件，用于对数组类型启用或选择实现。
<!-- cannbot:related:end -->
