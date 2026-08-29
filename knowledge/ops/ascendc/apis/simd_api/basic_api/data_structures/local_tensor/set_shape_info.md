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

- [ReduceShapeInfoOptimizeStack](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_shapeinfo_optimize_stack.md)（`explains`）：【描述】GlobalTensor和LocalTensor中通过ShapeInfo类型的成员变量来保存shape信息，SetShapeInfo/GetShapeInfo可以设置或者获取ShapeInfo，在算子实现内部用于shape信息保存和传递。默认情况下支持的最大维度为8。在不使用上述ShapeInfo功能的情况下，不需要这些信息，可以通过K_MAX_SHAPE_DIM宏将其设置为0。经实测减小K_MAX_SHAPE_DIM值，可缩减栈空间，减少scalar指令和cache miss几率，提升算子性能。；设置LocalTensor的Shape信息。；指南解释 LocalTensor 的 SetShapeInfo 所保存信息会占用栈空间，并给出未使用该能力时缩减 K_MAX_SHAPE_DIM 的优化条件，从而补充 API 使用成本与停用边界。
- [GetShapeInfo](get_shape_info.md)（`related`）：获取LocalTensor的Shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的Shape信息。；设置LocalTensor的Shape信息。。GetShapeInfo 的正确性前置条件就是先由 SetShapeInfo 写入属性，两接口构成 LocalTensor shape 元数据的写后读合同。
<!-- cannbot:related:end -->
