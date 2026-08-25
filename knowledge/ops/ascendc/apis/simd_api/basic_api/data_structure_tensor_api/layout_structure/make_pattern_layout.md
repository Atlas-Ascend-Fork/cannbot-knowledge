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

<!-- cannbot:related:start -->
## 相关

- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：MakePatternLayout 与《noTrans extract 与 NDExtLayoutPtn 方向不匹配》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [GetLayoutPattern](../utils/get_layout_pattern.md)（`related`）：MakePatternLayout 与《GetLayoutPattern》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [Layout](layout.md)（`related`）：MakePatternLayout 与《Layout》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`related`）：MakePatternLayout 与《Layout和层次化表述法》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeLayout](make_layout.md)（`related`）：MakePatternLayout 与《MakeLayout》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeShape](make_shape.md)（`related`）：MakePatternLayout 与《MakeShape》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeStride](make_stride.md)（`related`）：MakePatternLayout 与《MakeStride》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [基础API工具函数](../utils/tool_functions.md)（`related`）：GetLayoutPattern 的结果可用于构造/验证 PatternLayout。
- [MakeFrameLayout](make_frame_layout.md)（`same_topic`）：MakeFrameLayout 依据标准分形 Pattern/Trait 构造布局；MakePatternLayout 在已有 Shape/Stride 时显式携带同一 Pattern/Trait，是直接构造方式对照。
<!-- cannbot:related:end -->
