---
type: API
title: GetStride
description: 返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/GetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetStride

获取Layout的Stride信息。返回Layout中描述的各维度步长。函数原型：Stride GetStride() const。返回Stride结构体，包含各维度步长。用于查询Tensor的内存步长信息。

<!-- cannbot:related:start -->
## 相关

- [GetStride](../../data_structure_tensor_api/layout_structure/get_stride.md)（`same_topic`）：获取Layout的Stride信息。返回Layout中描述的各维度步长；从 Layout 中提取 Stride 部分。两端均定义从 Layout 读取 Stride 的同一操作，候选进一步给出 950 Tensor API 的 tuple 索引形态。
<!-- cannbot:related:end -->
