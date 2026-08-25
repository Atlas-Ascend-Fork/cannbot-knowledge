---
type: API
title: MakeFrameLayout
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 MakeFrameLayout用于根据标准分形排布模式构造带类型信息的Layout对象。该接口根据构造参数，结合指定的LayoutPattern（排布模式）和LayoutTrait（布局特征参数）计算Shape和Stride，构造Layout对象。除矩阵Layout外，该接口还支持构造卷积场景中的NCHW、NHWC和NC1HWC0格式Layout。该接口也支持在矩阵维度前传入Batch维度，用于构造多Batch矩阵的Layout。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeFrameLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MakeFrameLayout

试验接口。根据 LayoutPattern（排布模式）和 LayoutTrait（布局特征）计算 Shape 和 Stride，构造带类型信息的 Layout 对象。支持矩阵 Layout 和卷积 NCHW/NHWC/NC1HWC0 格式，支持 Batch 维度。头文件 `tensor_api/tensor.h`。

原型：`template <typename LayoutPattern, typename TraitType, typename... Args> MakeFrameLayout(const Args&... args)`。LayoutPattern 决定分形排列方式，不同存储位置间搬运要求特定 Pattern 组合。仅 950 支持。试验接口，不保证后续兼容性。

<!-- cannbot:related:start -->
## 相关

- [MakePatternLayout](make_pattern_layout.md)（`same_topic`）：MakeFrameLayout 依据标准分形 Pattern/Trait 构造布局；MakePatternLayout 在已有 Shape/Stride 时显式携带同一 Pattern/Trait，是直接构造方式对照。
<!-- cannbot:related:end -->
