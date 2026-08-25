---
type: API
title: is_convertible
description: is_convertible是定义于头文件的一个类型转换检查工具，它提供了一种在程序编译时进行类型转换检查的机制：判断两个类型之间是否可以进行隐式转换并返回结果布尔值。本接口可应用在模板元编程、函数重载决议以及静态断言等场景，用于在程序编译阶段捕获潜在的类型转换错误，避免发生运行时错误。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_convertible.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_convertible

is_convertible是定义于头文件的一个类型转换检查工具，它提供了一种在程序编译时进行类型转换检查的机制：判断两个类型之间是否可以进行隐式转换并返回结果布尔值。本接口可应用在模板元编程、函数重载决议以及静态断言等场景，用于在程序编译阶段捕获潜在的类型转换错误，避免发生运行时错误。

函数原型：template <typename From, typename To>；struct is_convertible;

参数：From：源类型，即需要进行转换的原始类型。；To：目标类型，即需要转换到的目标类型。

返回值：is_convertible的静态常量成员value用于获取返回的布尔值，is_convertible::value取值如下：

-   true：From类型的对象可以隐式转换为To类型。
-   false：From类型的对象不能隐式转换为To类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：源类型和目标类型均不支持抽象类和多态类型。

<!-- cannbot:related:start -->
## 相关

- [is_base_of](is_base_of.md)（`related`）：继承关系与隐式可转换性是模板约束中互补但不等价的判据；组合阅读可避免把私有继承或用户转换误当成 is_base_of。
- [is_pointer](is_pointer.md)（`related`）：is_pointer 与《is_convertible》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [is_same](is_same.md)（`related`）：is_same 要求完全相同，is_convertible 只要求可转换；API 约束强度不同。
- [Conditional](conditional.md)（`same_topic`）：is_convertible 与《Conditional》的实质衔接是：is_convertible 的编译期布尔值可直接送入 EnableIf/Conditional；is_same区分‘完全同型’与‘允许隐式转换’。
- [EnableIf](enable_if.md)（`same_topic`）：is_convertible 与《EnableIf》的实质衔接是：is_convertible 的编译期布尔值可直接送入 EnableIf/Conditional；is_same区分‘完全同型’与‘允许隐式转换’。
<!-- cannbot:related:end -->
