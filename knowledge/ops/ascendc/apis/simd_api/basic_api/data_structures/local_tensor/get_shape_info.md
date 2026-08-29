---
type: API
title: GetShapeInfo
description: 获取LocalTensor的Shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的Shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetShapeInfo

获取LocalTensor的Shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的Shape信息。

设置LocalTensor的Shape信息。

本接口组包含 SetShapeInfo, ShapeInfo。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [SetShapeInfo](set_shape_info.md)（`related`）：获取LocalTensor的Shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的Shape信息。；设置LocalTensor的Shape信息。。GetShapeInfo 的正确性前置条件就是先由 SetShapeInfo 写入属性，两接口构成 LocalTensor shape 元数据的写后读合同。
<!-- cannbot:related:end -->
