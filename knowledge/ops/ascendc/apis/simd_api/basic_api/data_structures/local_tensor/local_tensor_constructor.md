---
type: API
title: LocalTensor构造函数
description: LocalTensor构造函数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor构造函数

两种形式：Pipe 编程框架下 `LocalTensor<T>()` 默认构造（不赋初值，通常由 TQue 分配，开发者不直接调用）；静态 Tensor 编程下 `LocalTensor<T>(TPosition pos, uint32_t addr, uint32_t tileSize)` 或 `LocalTensor<T>(uint32_t addr)` 指定逻辑位置/地址/长度构造。模板参数 T 为数据类型。
