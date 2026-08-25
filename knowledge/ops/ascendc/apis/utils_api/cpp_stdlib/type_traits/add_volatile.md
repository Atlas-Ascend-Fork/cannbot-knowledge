---
type: API
title: add_volatile
description: 在程序编译时，为指定类型添加volatile限定符，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/add_volatile.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# add_volatile

在程序编译时，为指定类型添加volatile限定符，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct add_volatile;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、指针、引用）、用户自定义类型（如类、结构体等），以及带有volatile限定符的类型。

返回值：add_volatile是一个结构体，其提供一个嵌套类型type，表示添加volatile限定符后的类型。通过add_volatile::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
