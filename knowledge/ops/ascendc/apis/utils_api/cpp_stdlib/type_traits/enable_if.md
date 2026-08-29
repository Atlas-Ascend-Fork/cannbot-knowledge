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
