---
type: API
title: GetSize
description: 获取当前LocalTensor Size大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSize

获取当前LocalTensor Size大小。

获取当前LocalTensor Size大小。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：当前LocalTensor Size大小。单位为元素。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GetSize](../global_tensor/get_size.md)（`related`）：GlobalTensor 也暴露元素个数查询，可在 GM/Local 搬运两端核对 element count，但其存储域和初始化方式不同。
- [GetLength](get_length.md)（`same_topic`）：GetLength 返回 LocalTensor 占用字节数，而 GetSize 返回元素个数；二者共同界定同一张量容量并防止单位误用。
- [SetSize](set_size.md)（`same_topic`）：SetSize 与 GetSize 读写同一个 LocalTensor 元素计数属性，重用 tensor 并改变有效长度后可用 GetSize 复核。
<!-- cannbot:related:end -->
