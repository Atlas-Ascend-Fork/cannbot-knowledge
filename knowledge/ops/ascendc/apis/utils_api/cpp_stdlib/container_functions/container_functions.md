---
type: API
title: 容器函数
description: 提供tuple容器相关接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/container_functions/container_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 容器函数

提供 tuple 异构容器及相关辅助接口。tuple 允许聚合最多 64 个不同类型的元素，支持默认构造、初始化列表构造与复制构造，适用于多返回值封装、Tensor 聚合管理和模板元编程等场景。
get 按编译时常量索引从 tuple 中提取元素，索引范围为 [0, 64)；make_tuple 自动推断元素类型并创建 tuple 对象。两者支持 bool、各整型、half、bfloat16_t、fp8_e8m0_t、LocalTensor、GlobalTensor 等数据类型。
约束：不支持数组等可变长度类型；初始化列表中左值与右值不可混用；避免 tuple<int,int> = make_tuple(1,2,3) 这类因继承实现导致数据切片的写法。

<!-- cannbot:related:start -->
## 相关

- [Tuple](tuple.md)（`related`）：容器函数总览定义 tuple 的异构聚合、64 元素上限和限制，并导航到构造与访问接口。
<!-- cannbot:related:end -->
