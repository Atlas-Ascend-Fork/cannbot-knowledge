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

<!-- cannbot:related:start -->
## 相关

- [IntegralConstant](integral_constant.md)（`related`）：is_const 的结果以 integral_constant 风格暴露 value/type，理解该基类有助于在 enable_if 中消费判定结果。
- [add_const](add_const.md)（`related`）：“add_const”定义：在程序编译时，为指定类型添加const限定符，可以用于在编译时进行类型转换。；“is_const”定义：在程序编译时，检测一个类型是否为const限定的类型，可以用于在编译时进行类型检查和条件处理。。实质衔接：add_const 添加限定，is_const 验证结果，remove_const 执行逆变换，add_cv 同时添加 const/volatile。
- [remove_const](remove_const.md)（`related`）：is_const 在编译期检测顶层 const，remove_const 根据该属性规范化类型，构成检测—变换链。
- [add_volatile](add_volatile.md)（`same_topic`）：is_const说明在程序编译时，检测一个类型是否为const限定的类型，可以用于在编译时进行类型检查和条件处理。
<!-- cannbot:related:end -->
