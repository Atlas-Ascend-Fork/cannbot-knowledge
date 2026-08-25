---
type: API
title: GetLength
description: 获取LocalTensor数据长度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetLength.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLength

获取LocalTensor数据长度。

获取LocalTensor数据长度。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：LocalTensor数据长度，单位为字节。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GetSize](get_size.md)（`same_topic`）：GetLength 返回 LocalTensor 占用字节数，而 GetSize 返回元素个数；二者共同界定同一张量容量并防止单位误用。
<!-- cannbot:related:end -->
