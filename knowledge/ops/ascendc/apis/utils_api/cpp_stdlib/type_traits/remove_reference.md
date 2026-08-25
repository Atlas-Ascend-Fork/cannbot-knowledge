---
type: API
title: remove_reference
description: 在程序编译时，从给定类型中移除引用限定符，包括左值引用T&和右值引用T&&，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/remove_reference.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# remove_reference

在程序编译时，从给定类型中移除引用限定符，包括左值引用T&和右值引用T&&，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct remove_reference;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、指针）、用户自定义类型（如类、结构体等），以及带有左值引用&或右值引用&&限定的类型。

返回值：remove_reference是一个结构体，其提供一个嵌套类型type，表示移除引用限定符后的类型。通过remove_reference::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [add_lvalue_reference](add_lvalue_reference.md)（`related`）：add_lvalue_reference 与 remove_reference 对同一左值引用限定做添加和消除，是模板参数规范化后的逆向变换。
- [is_reference](is_reference.md)（`related`）：is_reference 先判定 Tp 是否为 T&/T&&，remove_reference 再把引用类型规范化为底层类型，是泛型分派中的检测—变换链。
- [add_rvalue_reference](add_rvalue_reference.md)（`same_topic`）：remove_reference 是添加引用的逆变换，可恢复基础类型后继续类型判断。
<!-- cannbot:related:end -->
