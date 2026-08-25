---
type: API
title: IntegralConstant
description: 封装编译时常量整数值的模板结构体，是类型特性和编译时计算的基础组件，支持隐式转换和函数调用运算符。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/integral_constant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# integral_constant

integral_constant是一个带有模板参数的结构体，定义在头文件中，用于封装一个编译时常量整数值，是标准库中许多类型特性和编译时计算的基础组件。

integral_constant的功能如下：

1.  封装编译时常量，将一个int或bool类型的值封装为特定类型，以便该值可以在编译时被操作和传递。
2.  类型标识，每个不同的integral_constant实例都是唯一的类型，可用于模板特化或重载决议。
3.  隐式转换时支持转换为其封装的值类型，便于在需要该值的上下文中直接使用。
4.  函数调用运算符允许像调用函数一样调用实例，以获取其值。

integral_constant提供了多个常用的特化版本，具体如下：

-   Std::true_type：integral_constant的别名。
-   Std::false_type：integral_constant的别名。
-   数值常量：如Std::integral_constant。
-   数值常量的简化写法，Std::Int，数值类型为size_t：如Std::Int。

函数原型：template <typename Tp, Tp v>；struct integral_constant；{ 等11种重载

参数：Tp：数值的数据类型。；v：常量数值。

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   Int类型是integral_constant数值结构的别名简写，数值类型必须是size_t类型。
-   模板参数Tp不支持float等浮点数类型，因为模板参数需在编译期确定，而浮点数的精度问题可能导致编译期无法准确表示。
