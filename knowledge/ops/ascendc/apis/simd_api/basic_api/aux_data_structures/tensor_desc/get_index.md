---
type: API
title: GetIndex
description: 获取TensorDesc在ListTensorDesc中对应的索引值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetIndex.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# GetIndex

获取TensorDesc在ListTensorDesc中对应的索引值。

获取TensorDesc在ListTensorDesc中对应的索引值。

本接口属于 Tensor 数据结构操作接口。

返回值：返回TensorDesc在ListTensorDesc中对应的索引值。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

<!-- cannbot:related:start -->
## 相关

- [GetDataObj](get_data_obj.md)（`related`）：GetIndex说明获取TensorDesc在ListTensorDesc中对应的索引值；对GetDataObj而言，GetDataObj 返回的对象需按 TensorDesc 的 data pointer 与 index 契约解释，不能把描述对象当作裸数据地址。
<!-- cannbot:related:end -->
