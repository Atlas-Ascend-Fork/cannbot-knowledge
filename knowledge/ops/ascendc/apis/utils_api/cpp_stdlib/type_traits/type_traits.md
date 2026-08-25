---
type: API
title: Utils API类型特性
description: type_traits是Ascend C标准库中的一个头文件（），它提供了一系列用于在编译时进行类型检查、类型转换和类型操作的模板元编程工具。这些工具可以帮助开发者在程序编译时进行类型相关的决策，从而提高代码的安全性和性能。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/type_traits/type_traits.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Utils API类型特性

type_traits 是 Ascend C 标准库提供的头文件（<type_traits>），用于编译时类型检查、类型转换和类型操作的模板元编程。提供类型判断（is_integral、is_pointer、is_const 等）、CV 属性移除与添加（remove_const、add_pointer 等）和条件编译辅助（enable_if、conditional）等工具，帮助在编译期进行类型相关决策。

<!-- cannbot:related:start -->
## 相关

- [C++标准库](../cpp_stdlib.md)（`same_topic`）：Utils API类型特性 与《C++标准库》的实质衔接是：该卡是 type_traits 能力总览，具体成员由 part_of 导航；C++ 标准库概述提供其所在标准库边界。
<!-- cannbot:related:end -->
