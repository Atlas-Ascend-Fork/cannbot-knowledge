---
type: API
title: MakeLayout
description: 根据Shape和Stride构造Layout对象，描述数据张量在逻辑维度上的形状及各维步长信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MakeLayout

根据Shape和Stride构造Layout对象，描述数据张量在逻辑维度上的形状及各维步长信息。

构造Shape对象，用于描述数据的逻辑形状。支持传入多个维度值，也支持传入嵌套的Shape子结构以构造层次化Shape。

本接口组包含 MakeShape, MakeStride, MakePatternLayout，辅助接口包括 GetLayoutPattern。

返回值：返回Shape 对象。

约束：输入参数不可为空；输入的参数为正整数。；支持的数据类型包括：size_t、int等整数类型或者Std::Int类型。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetLayoutPattern](../utils/get_layout_pattern.md)（`related`）：MakeLayout 可按 shape/stride 推导 LayoutPattern，GetLayoutPattern 用于核验推导结果或识别歧义返回 ignore。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`related`）：层次化表述最终仍由嵌套 Shape 与 Stride 构造 Layout；MakeLayout 是把该表述落成可索引对象的基础入口。
- [MakePatternLayout](make_pattern_layout.md)（`related`）：MakePatternLayout 与《MakeLayout》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeShape](make_shape.md)（`related`）：MakeLayout 明确以 MakeShape 产出的 Shape 和 Stride 构造排布对象，直接给出 focal 结果的下游使用点。
- [MakeStride](make_stride.md)（`related`）：MakeLayout 消费 MakeShape 与 MakeStride 的结果形成可寻址布局，是 MakeStride 的直接下游。
- [MakeTensor](../tensor_structure/make_tensor.md)（`related`）：MakeTensor 的第二项必需输入是 MakeLayout 生成的 Shape/Stride 布局；编译器联合该布局与 MemPtr Engine 选择 Copy/Mmad 指令。
- [Select（基础API）](select.md)（`related`）：Select 消费一个已有 Layout 并同时抽取其 shape/stride 指定维度；MakeLayout 说明该 Layout 本来由 Shape 和 Stride 组成，是 Select 的直接上游对象构造。
- [Shape（基础API）](shape.md)（`related`）：MakeLayout 消费 Shape 与 Stride 构造寻址布局，是 Shape 的直接下游。
- [Stride（基础API）](stride.md)（`related`）：MakeLayout 消费 Shape 与 Stride 形成寻址映射，是 Stride 的直接下游。
- [GetShape](get_shape.md)（`same_topic`）：GetShape说明需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [GetStride](get_stride.md)（`same_topic`）：GetStride说明需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [Layout](layout.md)（`same_topic`）：Layout说明Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
- [MakeLayout](../../aux_data_structures/layout/make_layout.md)（`same_topic`）：MakeLayout 与《MakeLayout》的实质衔接是：MakeLayout 将 MakeShape 和 MakeStride 的结果组合为 Layout；直接构造函数是等价构造路径，Crd2Idx 以该 Layout 做坐标到地址映射，Layout 概念卡解释 shape/stride 的内存契约。
- [基础APIRank](rank.md)（`same_topic`）：基础APIRank 与《MakeLayout》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《MakeLayout》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
