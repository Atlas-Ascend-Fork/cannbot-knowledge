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
