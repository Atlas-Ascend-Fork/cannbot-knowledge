---
type: API
title: SetShapeInfo
description: 设置GlobalTensor的shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetShapeInfo

设置GlobalTensor的shape信息。

设置GlobalTensor的shape信息。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

返回值：无。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GetShapeInfo](get_shape_info.md)（`related`）：设置GlobalTensor的shape信息。；获取GlobalTensor的shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的ShapeInfo。。GetShapeInfo 明确依赖此前由 SetShapeInfo 写入的 shape 元数据，两接口形成同一 GlobalTensor 属性的写后读契约。
<!-- cannbot:related:end -->
