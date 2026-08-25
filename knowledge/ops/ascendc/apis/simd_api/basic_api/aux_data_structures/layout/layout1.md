---
type: API
title: layout
description: 获取Layout实例化对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/layout1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout结构体定义

Layout结构体用于描述Tensor的数据排布，包含shape（各维度大小）、stride（各维度步长）和format（数据格式）等成员。Layout支持ND格式（连续排布）和NZ格式（分块排布）等。通过Layout可以描述Tensor在内存中的完整排布信息，用于DataCopy等操作的数据搬运。
