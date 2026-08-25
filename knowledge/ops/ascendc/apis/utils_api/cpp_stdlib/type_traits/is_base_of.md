---
type: API
title: is_base_of
description: is_base_of是定义于头文件的一个类型特征工具，它能够在程序编译时检查一个类型是否为另一个类型的基类。本接口可应用在模板元编程、类型检查和条件编译等场景，用于在编译阶段捕获潜在的类型错误，提高代码的鲁棒性。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/is_base_of.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# is_base_of

is_base_of是定义于头文件的一个类型特征工具，它能够在程序编译时检查一个类型是否为另一个类型的基类。本接口可应用在模板元编程、类型检查和条件编译等场景，用于在编译阶段捕获潜在的类型错误，提高代码的鲁棒性。

函数原型：template <typename Base, typename Derived>；struct is_base_of;

参数：Base：待检查的基类类型，即Base类型是否为Derived类型的基类。；Derived：待检查的派生类类型，即Base类型是否为Derived类型的基类。

返回值：is_base_of的静态常量成员value用于获取返回的布尔值，is_base_of::value取值如下：

-   true：Base类型是Derived类型的基类（包括Base类型和Derived类型为同一类型的情况）。
-   false：Base类型不是Derived类型的基类。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [EnableIf](enable_if.md)（`related`）：is_base_of 产出的编译期 bool 可直接作为 enable_if 条件，以基类关系启用或禁用模板重载。
- [is_convertible](is_convertible.md)（`related`）：继承关系与隐式可转换性是模板约束中互补但不等价的判据；组合阅读可避免把私有继承或用户转换误当成 is_base_of。
<!-- cannbot:related:end -->
