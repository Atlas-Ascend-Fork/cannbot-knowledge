---
type: API
title: GetStride
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分：
  - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/GetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GetStride

从 Layout 中提取 Stride 部分。不指定模板参数返回完整 Stride 元组；指定 Is... 从顶层 tuple 选择对应索引元素。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [GetStride](../../aux_data_structures/layout/get_stride.md)（`same_topic`）：获取Layout的Stride信息。返回Layout中描述的各维度步长；从 Layout 中提取 Stride 部分。两端均定义从 Layout 读取 Stride 的同一操作，候选进一步给出 950 Tensor API 的 tuple 索引形态。
<!-- cannbot:related:end -->
