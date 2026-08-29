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

- [SetSize](set_size.md)（`related`）：返回值：当前LocalTensor Size大小。单位为元素。；设置当前LocalTensor Size大小。单位为元素。当用户重用local tensor变量且使用长度发生变化的时候，需要使用此接口重新设置Size。。SetSize 在 LocalTensor 重用长度变化时更新元素数，GetSize 读取同一元素单位的当前值，构成 Size 属性的写后读操作。
<!-- cannbot:related:end -->
