---
type: API
title: remove_const
description: 在程序编译时，对传入的模板参数类型移除const限定符，可以用于在编译时进行类型转换。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/remove_const.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# remove_const

在程序编译时，对传入的模板参数类型移除const限定符，可以用于在编译时进行类型转换。

函数原型：template <typename Tp>；struct remove_const;

参数：Tp：需要处理的类型，包括基本类型（如int、float等）、复合类型（如数组、指针、引用）、用户自定义类型（如类、结构体等），以及const限定的类型。

返回值：remove_const是一个结构体，其提供一个嵌套类型type，表示移除const限定符后的类型。通过remove_const::type来访问该类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [add_const](add_const.md)（`related`）：“add_const”定义：在程序编译时，为指定类型添加const限定符，可以用于在编译时进行类型转换。；“remove_const”定义：在程序编译时，对传入的模板参数类型移除const限定符，可以用于在编译时进行类型转换。。实质衔接：add_const 添加限定，is_const 验证结果，remove_const 执行逆变换，add_cv 同时添加 const/volatile。
- [is_const](is_const.md)（`related`）：is_const 在编译期检测顶层 const，remove_const 根据该属性规范化类型，构成检测—变换链。
- [remove_cv](remove_cv.md)（`same_topic`）：remove_const 只去掉 const，remove_cv 同时去掉 const 与 volatile；后者是组合变换，适合需要完全规范化 cv 限定的模板。
<!-- cannbot:related:end -->
