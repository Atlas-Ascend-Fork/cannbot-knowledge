---
type: API
title: 运算符重载
description: 重载运算符\(\)，内部实现为调用Crd2Idx接口，将多维坐标（Coordinate）通过布局（Layout）转换为内存位置索引（Index）。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/operator_overloading.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout运算符重载

Layout支持operator==运算符重载，用于判断两个Layout是否相等。比较shape、stride和format等所有属性，全部相同则返回true。用于在运算前验证输入输出Tensor的Layout一致性。
