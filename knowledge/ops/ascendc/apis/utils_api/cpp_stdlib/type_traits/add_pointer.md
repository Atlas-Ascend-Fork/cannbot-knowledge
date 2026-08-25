---
type: API
title: add_pointer
description: 在程序编译时，为指定类型添加指针限定符，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/add_pointer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# add_pointer

在程序编译时，为指定类型添加指针限定符，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct add_pointer;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、引用）以及带有指针限定符的类型。

返回值：add_pointer是一个结构体，其提供一个嵌套类型type，表示添加指针限定符后的类型。通过add_pointer::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [is_pointer](is_pointer.md)（`same_topic`）：add_pointer：add_pointer与remove_pointer构成互逆类型变换，is_pointer可在模板分支中验证变换结果；其他不相关 trait不连接。 目标卡《is_pointer》补充：在程序编译时，判断一个类型是否为指针类型，可以用于在编译时进行类型检查和条件处理。
- [remove_pointer](remove_pointer.md)（`same_topic`）：add_pointer：add_pointer与remove_pointer构成互逆类型变换，is_pointer可在模板分支中验证变换结果；其他不相关 trait不连接。 目标卡《remove_pointer》补充：在程序编译时，从给定类型中移除指针限定符，可以用于在编译时进行类型转换。
<!-- cannbot:related:end -->
