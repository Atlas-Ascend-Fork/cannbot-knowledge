---
type: API
title: Conditional
description: 编译时类型特征工具，根据布尔条件从两个类型中选择一个，用于模板元编程中的类型选择。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/conditional.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# conditional

conditional是定义在头文件里的一个类型特征工具，它在程序编译时根据一个布尔条件从两个类型中选择一个类型。本接口可应用在模板元编程中，用于根据不同的条件来灵活选择合适的类型，增强代码的通用性和灵活性。

conditional有一个嵌套的type成员，它的值取决于Bp的值：如果Bp为true，则conditional::type为If。如果Bp为false，则conditional::type为Then。

函数原型：template <bool Bp, typename If, typename Then>；struct conditional;

参数：Bp：一个布尔常量表达式，作为选择类型的条件。；If：当Bp为true时选择的类型。；Then：当Bp为false时选择的类型。

返回值：conditional的静态常量成员type用于获取返回值，conditional::type取值如下：

-   If：Bp为true。
-   Then：Bp为false。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [EnableIf](enable_if.md)（`related`）：EnableIf 用条件决定模板是否参与重载，Conditional 用同一编译期布尔条件选择结果类型；二者可组合构建类型分支。
- [is_array](is_array.md)（`related`）：is_array 与《Conditional》的衔接是：is_array 的布尔 trait 结果可直接作为 Conditional/EnableIf 的编译期条件，用于对数组类型启用或选择实现。
- [is_pointer](is_pointer.md)（`related`）：is_pointer 与《Conditional》的实质衔接是：is_pointer 的结果常与 add/remove_pointer 组成归一化判断，并由 conditional/EnableIf 驱动模板分支；is_same/is_convertible 用于限定分支中的目标类型契约。
- [is_same](is_same.md)（`related`）：conditional 可据 is_same 结果选择返回类型或实现类型。
- [IntegralConstant](integral_constant.md)（`same_topic`）：Conditional：Conditional按编译期bool选择类型，EnableIf据条件启用模板而IntegralConstant承载编译期常量；三者可共同实现可验证的类型分发。 目标卡《IntegralConstant》补充：封装编译时常量整数值的模板结构体，是类型特性和编译时计算的基础组件，支持隐式转换和函数调用运算符。
- [is_convertible](is_convertible.md)（`same_topic`）：is_convertible 与《Conditional》的实质衔接是：is_convertible 的编译期布尔值可直接送入 EnableIf/Conditional；is_same区分‘完全同型’与‘允许隐式转换’。
- [is_void](is_void.md)（`same_topic`）：is_void 与《Conditional》的实质衔接是：is_void 常与 integral_constant/is_same 表达编译期结果，并通过 Conditional/EnableIf 选择仅对 void 或非 void 有效的模板实现。
- [remove_pointer](remove_pointer.md)（`same_topic`）：remove_pointer 与《Conditional》的实质衔接是：remove_pointer 与 add_pointer/is_pointer 构成指针类型归一化，随后常用 is_same、Conditional 或 EnableIf 约束模板分支。
<!-- cannbot:related:end -->
