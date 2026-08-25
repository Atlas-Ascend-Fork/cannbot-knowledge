---
type: API
title: ListTensorDesc
description: ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/ListTensorDesc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# ListTensorDesc

ListTensorDesc是Tensor描述符列表，用于管理多个Tensor的描述信息。支持添加、获取和遍历TensorDesc，常用于需要同时处理多个Tensor的场景（如多头注意力等）。

提供构造函数创建空列表，通过AppendTensorDesc添加Tensor描述符，通过GetTensorDesc获取指定位置的描述符，通过GetNum获取列表大小。ListTensorDesc与TBuf配合使用，管理多个LocalTensor的分配。
