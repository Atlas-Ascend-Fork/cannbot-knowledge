---
type: API
title: EnableIf
description: 编译时模板元编程工具，根据布尔条件启用或禁用特定的函数模板、类模板或模板特化。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/enable_if.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# enable_if

enable_if是定义于头文件的一个模板元编程工具，它能够在程序编译时根据某个条件启用或禁用特定的函数模板、类模板或模板特化，以此实现更精细的模板重载和类型选择，增强代码的灵活性和安全性。

enable_if是一个模板结构体，有两个模板参数：模板参数Bp是一个布尔值，表示条件；模板参数Tp是一个类型，默认值为void。当Bp为false时，enable_if没有嵌套的type成员。当Bp为true时，enable_if有一个嵌套的type成员，其类型为Tp。

函数原型：template <bool Bp, typename Tp>；struct enable_if;

参数：Bp：布尔值，表示条件。；Tp：类型，默认值为void。

返回值：enable_if的静态常量成员type用于获取返回值，enable_if::type取值如下：

-   Tp：Bp为true。
-   void：Bp为false。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Conditional](conditional.md)（`related`）：EnableIf 用条件决定模板是否参与重载，Conditional 用同一编译期布尔条件选择结果类型；二者可组合构建类型分支。
- [is_array](is_array.md)（`related`）：is_array 与《EnableIf》的衔接是：is_array 的布尔 trait 结果可直接作为 Conditional/EnableIf 的编译期条件，用于对数组类型启用或选择实现。
- [is_base_of](is_base_of.md)（`related`）：is_base_of 产出的编译期 bool 可直接作为 enable_if 条件，以基类关系启用或禁用模板重载。
- [is_floating_point](is_floating_point.md)（`related`）：is_floating_point 的编译期 value 可直接作为 enable_if 条件，为浮点专用函数模板或特化启用路径。
- [is_integral](is_integral.md)（`related`）：enable_if 可直接消费 is_integral 结果约束模板重载，连接判定与编译期分派。
- [is_pointer](is_pointer.md)（`related`）：is_pointer 与《EnableIf》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [is_same](is_same.md)（`related`）：enable_if 可消费 is_same 结果选择特化路径，连接类型等同性判定与编译期分派。
- [IntegralConstant](integral_constant.md)（`same_topic`）：EnableIf说明编译时模板元编程工具，根据布尔条件启用或禁用特定的函数模板、类模板或模板特化。
- [is_convertible](is_convertible.md)（`same_topic`）：is_convertible 与《EnableIf》的实质衔接是：is_convertible 的编译期布尔值可直接送入 EnableIf/Conditional；is_same区分‘完全同型’与‘允许隐式转换’。
- [is_void](is_void.md)（`same_topic`）：is_void 与《EnableIf》的实质衔接是：is_void 常与 integral_constant/is_same 表达编译期结果，并通过 Conditional/EnableIf 选择仅对 void 或非 void 有效的模板实现。
- [remove_pointer](remove_pointer.md)（`same_topic`）：remove_pointer 与《EnableIf》的实质衔接是：remove_pointer 与 add_pointer/is_pointer 构成指针类型归一化，随后常用 is_same、Conditional 或 EnableIf 约束模板分支。
<!-- cannbot:related:end -->
