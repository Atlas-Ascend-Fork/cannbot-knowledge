---
type: API
title: ShapeInfo（辅助数据结构）
description: ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/ShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# ShapeInfo

ShapeInfo是Tensor形状信息结构体，用于描述Tensor的维度数和各维度大小。支持最多8维shape描述。

提供构造函数（通过shape数组或各维度值构造）、GetDimNum获取维度数、GetDim获取指定维度大小等接口。ShapeInfo用于TensorDesc和Layout中描述Tensor的形状。
