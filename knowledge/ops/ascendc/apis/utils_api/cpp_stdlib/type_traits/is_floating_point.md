---
type: API
title: is_floating_point
description: 在程序编译时，检测一个类型是否为浮点类型，可以用于在编译时进行类型检查和条件处理。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_floating_point.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_floating_point

在程序编译时，检测一个类型是否为浮点类型，可以用于在编译时进行类型检查和条件处理。

函数原型：template <typename T>；struct is_floating_point;

参数：T：需要检测的类型，包括基本数据类型、修饰类型等。

返回值：is_floating_point的静态常量成员value用于获取返回的布尔值，is_floating_point::value取值如下：

-   true：Tp是浮点类型。
-   false：Tp不是浮点类型。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [EnableIf](enable_if.md)（`related`）：is_floating_point 的编译期 value 可直接作为 enable_if 条件，为浮点专用函数模板或特化启用路径。
- [is_integral](is_integral.md)（`related`）：is_floating_point 与 is_integral 是数值模板分派的互补判据，可避免把整数和浮点实现落入同一精度/指令路径。
<!-- cannbot:related:end -->
