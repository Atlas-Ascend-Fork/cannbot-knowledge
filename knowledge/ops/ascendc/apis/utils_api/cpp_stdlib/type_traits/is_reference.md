---
type: API
title: is_reference
description: 在程序编译时，检测一个类型是否为引用类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_reference.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_reference

在程序编译时，检测一个类型是否为引用类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename Tp>；struct is_reference;

参数：Tp：需要检测的类型，包括基本类型（如int、float等）、复合类型（如数组、指针）、用户自定义类型（如类、结构体等），以及引用类型本身。

返回值：is_reference的静态常量成员value用于获取返回的布尔值，is_reference::value取值如下：

-   true：Tp是引用类型。
-   false：Tp不是引用类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [add_lvalue_reference](add_lvalue_reference.md)（`related`）：add_lvalue_reference 构造 T&，is_reference 可验证构造后的类型是否落入引用分支；二者用于编译期引用限定的生成与检查。
- [remove_reference](remove_reference.md)（`related`）：is_reference 先判定 Tp 是否为 T&/T&&，remove_reference 再把引用类型规范化为底层类型，是泛型分派中的检测—变换链。
<!-- cannbot:related:end -->
