---
type: API
title: MakePatternLayout
description: 根据Shape、Stride、LayoutPattern和TraitType构造带布局模式信息的Layout对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakePatternLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MakePatternLayout

根据 Shape、Stride、LayoutPattern 和 TraitType 构造带布局模式信息的 Layout 对象。头文件为 tensor_api/tensor.h。
相比 MakeLayout 仅保存 Shape 和 Stride，MakePatternLayout 还在 Layout 类型中附加布局模式 LayoutPattern 与 Trait 信息，用于描述 C0 粒度等布局特征。
TraitType 使用 LayoutTrait<T, C0> 或 LayoutTraitDefault<T> 写法时，T 仅作为兼容占位或 C0 推导依据，不作为 Tensor 数据类型保存。
返回 Layout<ShapeType, StrideType, Std::tuple<LayoutPattern, TraitType>> 类型对象。
约束：shape 与 stride 必须为元组类型；LayoutPattern 应为 NZLayoutPtn、ZNLayoutPtn、NDLayoutPtn、DNLayoutPtn 等合法类型。仅 Ascend 950PR/950DT 支持。
