---
type: API
title: SetShapeInfo
description: 设置LocalTensor的Shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetShapeInfo

设置LocalTensor的Shape信息。

设置LocalTensor的Shape信息。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [ReduceShapeInfoOptimizeStack](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_shapeinfo_optimize_stack.md)（`explains`）：ReduceShapeInfoOptimizeStack 与《SetShapeInfo》的实质衔接是：该优化通过 K_MAX_SHAPE_DIM 缩减 GlobalTensor/LocalTensor 的 ShapeInfo；Get/SetShapeInfo 与 ShapeInfo结构是确认是否真的需要这些栈字段的直接依据。
- [GetShapeInfo](../global_tensor/get_shape_info.md)（`related`）：GetShapeInfo 与《SetShapeInfo》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetShapeInfo](../global_tensor/set_shape_info.md)（`related`）：《SetShapeInfo》明确“设置LocalTensor的Shape信息。”；它与《SetShapeInfo》的“设置GlobalTensor的shape信息。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetShapeInfo](get_shape_info.md)（`same_topic`）：GetShapeInfo 只有在同一个 LocalTensor 已通过 SetShapeInfo 设置有效 ShapeInfo 后才可读取，二者组成读写契约。
- [ShapeInfo（辅助数据结构）](../../aux_data_structures/shape_info.md)（`same_topic`）：LocalTensor::SetShapeInfo 负责把 ShapeInfo 写入 UB Tensor 属性，与结构体的构造和维度访问能力直接配套。
<!-- cannbot:related:end -->
