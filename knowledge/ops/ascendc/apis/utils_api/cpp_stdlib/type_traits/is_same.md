---
type: API
title: is_same
description: is_same是定义在头文件里的一个类型特征工具，它能够在程序编译时判断两个类型是否完全相同。本接口可应用在模板元编程、类型检查、条件编译等场景，用于在编译阶段确定类型信息，避免运行时可能出现的类型不匹配问题。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_same.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_same

is_same是定义在头文件里的一个类型特征工具，它能够在程序编译时判断两个类型是否完全相同。本接口可应用在模板元编程、类型检查、条件编译等场景，用于在编译阶段确定类型信息，避免运行时可能出现的类型不匹配问题。

函数原型：template <typename Tp, typename Up>；struct is_same;

参数：Tp：需要比较两个类型是否完全相同的第一个类型。；Up：需要比较两个类型是否完全相同的第二个类型。

返回值：is_same的静态常量成员value用于获取返回的布尔值，is_same::value取值如下：

-   true：Tp和Up是完全相同的类型。
-   false：Tp和Up不是相同的类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
