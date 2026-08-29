---
type: API
title: 构造和析构函数
description: 创建与释放TensorDesc对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# TensorDesc构造与析构函数

TensorDesc提供默认构造函数（创建空描述符）、通过shape和data type构造、拷贝构造等。析构函数释放相关资源。构造参数可包含shape信息、数据类型、layout等。构造的TensorDesc用于描述Tensor的元信息。
