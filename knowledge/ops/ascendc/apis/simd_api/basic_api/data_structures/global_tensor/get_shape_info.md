---
type: API
title: GetShapeInfo
description: 获取GlobalTensor的shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的ShapeInfo。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetShapeInfo

获取GlobalTensor的shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的ShapeInfo。

ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。

本接口组包含 ShapeInfo。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [StorageShape scalar GetShapeSize 返回 1](../../../../../runbooks/compilation/gert_storage_shape_scalar_getshapesize_returns_one.md)（`exemplifies`）：GetShapeInfo 与《StorageShape scalar GetShapeSize 返回 1》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [ReduceShapeInfoOptimizeStack](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_shapeinfo_optimize_stack.md)（`explains`）：ReduceShapeInfoOptimizeStack 与《GetShapeInfo》的实质衔接是：该优化通过 K_MAX_SHAPE_DIM 缩减 GlobalTensor/LocalTensor 的 ShapeInfo；Get/SetShapeInfo 与 ShapeInfo结构是确认是否真的需要这些栈字段的直接依据。
- [GetShapeInfo](../local_tensor/get_shape_info.md)（`related`）：GetShapeInfo 与《GetShapeInfo》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [GlobalTensor](global_tensor.md)（`related`）：GetShapeInfo 与《GlobalTensor》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [GlobalTensor简介](global_tensor_intro.md)（`related`）：GetShapeInfo 与《GlobalTensor简介》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetGlobalBuffer](set_global_buffer.md)（`related`）：GetShapeInfo 与《SetGlobalBuffer》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetShape](../../../adv_api/cube_compute/matmul_tiling/set_shape.md)（`related`）：GetShapeInfo 与《SetShape》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetShapeAddr](../../aux_data_structures/tensor_desc/set_shape_addr.md)（`related`）：GetShapeInfo 与《SetShapeAddr》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetShapeInfo](set_shape_info.md)（`related`）：《GetShapeInfo》明确“获取GlobalTensor的shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的ShapeInfo。”；它与《SetShapeInfo》的“设置GlobalTensor的shape信息。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetShapeInfo](../local_tensor/set_shape_info.md)（`related`）：GetShapeInfo 与《SetShapeInfo》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [TensorShape](../../../adv_api/data_structures/tensor_shape.md)（`related`）：GetShapeInfo 与《TensorShape》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [ShapeInfo（辅助数据结构）](../../aux_data_structures/shape_info.md)（`same_topic`）：GlobalTensor::GetShapeInfo 返回的正是 ShapeInfo 结构，并要求先通过 SetShapeInfo 初始化。
<!-- cannbot:related:end -->
