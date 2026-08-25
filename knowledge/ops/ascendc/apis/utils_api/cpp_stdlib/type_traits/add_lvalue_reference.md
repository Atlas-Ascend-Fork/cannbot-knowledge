---
type: API
title: add_lvalue_reference
description: 在程序编译时，为指定类型添加左值引用限定符，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/add_lvalue_reference.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# add_lvalue_reference

在程序编译时，为指定类型添加左值引用限定符，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct add_lvalue_reference;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、指针）、用户自定义类型（如类、结构体等），以及带有引用限定符的类型。

返回值：add_lvalue_reference是一个结构体，其提供一个嵌套类型type，表示添加左值引用限定符后的类型。通过add_lvalue_reference::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [is_reference](is_reference.md)（`related`）：add_lvalue_reference 构造 T&，is_reference 可验证构造后的类型是否落入引用分支；二者用于编译期引用限定的生成与检查。
- [remove_reference](remove_reference.md)（`related`）：add_lvalue_reference 与 remove_reference 对同一左值引用限定做添加和消除，是模板参数规范化后的逆向变换。
- [add_rvalue_reference](add_rvalue_reference.md)（`same_topic`）：add_lvalue_reference 与 add_rvalue_reference 为同一类型分别添加左值/右值引用，是引用类别驱动的直接选择。
<!-- cannbot:related:end -->
