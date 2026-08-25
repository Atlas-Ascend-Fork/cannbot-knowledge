---
type: API
title: ShapeInfo（辅助数据结构）
description: ShapeInfo用来存放LocalTensor或GlobalTensor的shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/ShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# ShapeInfo

ShapeInfo是Tensor形状信息结构体，用于描述Tensor的维度数和各维度大小。支持最多8维shape描述。

提供构造函数（通过shape数组或各维度值构造）、GetDimNum获取维度数、GetDim获取指定维度大小等接口。ShapeInfo用于TensorDesc和Layout中描述Tensor的形状。

<!-- cannbot:related:start -->
## 相关

- [ReduceShapeInfoOptimizeStack](../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_shapeinfo_optimize_stack.md)（`explains`）：ReduceShapeInfoOptimizeStack 与《ShapeInfo（辅助数据结构）》的实质衔接是：该优化通过 K_MAX_SHAPE_DIM 缩减 GlobalTensor/LocalTensor 的 ShapeInfo；Get/SetShapeInfo 与 ShapeInfo结构是确认是否真的需要这些栈字段的直接依据。
- [GetShapeInfo](../data_structures/global_tensor/get_shape_info.md)（`same_topic`）：GlobalTensor::GetShapeInfo 返回的正是 ShapeInfo 结构，并要求先通过 SetShapeInfo 初始化。
- [GetShapeInfo](../data_structures/local_tensor/get_shape_info.md)（`same_topic`）：LocalTensor::GetShapeInfo 使用同一 ShapeInfo 类型读取 UB Tensor 的最多八维形状。
- [SetShapeInfo](../data_structures/global_tensor/set_shape_info.md)（`same_topic`）：GlobalTensor::SetShapeInfo 将 ShapeInfo 写入 GM Tensor 属性，是该结构在 GlobalTensor 上的设置入口。
- [SetShapeInfo](../data_structures/local_tensor/set_shape_info.md)（`same_topic`）：LocalTensor::SetShapeInfo 负责把 ShapeInfo 写入 UB Tensor 属性，与结构体的构造和维度访问能力直接配套。
<!-- cannbot:related:end -->
