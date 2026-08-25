---
type: API
title: Layout
description: Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Layout

试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。

核心方法：Shape()/Stride() 获取形状/步长，Capacity() 内存容量，Size() 有效元素数，Rank() 秩，Get/Select 提取子 Layout，Squeeze 删除 size=1 维度，Coshape/Cosize 陪域大小。支持层次化表述法（元素可为元组）描述 NZ/Zz/Zn 等分形格式。试验接口，不保证后续兼容性。

<!-- cannbot:related:start -->
## 相关

- [GetShape](get_shape.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《GetShape》补充：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [GetStride](get_stride.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《GetStride》补充：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [MakePatternLayout](make_pattern_layout.md)（`related`）：MakePatternLayout 与《Layout》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [Tensor](../tensor_structure/tensor.md)（`related`）：Tensor 的地址映射由内含 Layout 的 Shape/Stride 决定；Layout 卡提供 Capacity、Size、Rank 及层次化分形表达，直接解释 Tensor 如何定位元素。
- [基础APIGet](get.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“Layout”定义：Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [基础APIRank](rank.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《基础APIRank》补充：用于返回Layout的秩。
- [Coord（基础API）](coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout正文说明“Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`same_topic`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《Layout和层次化表述法》补充：Layout通过Shape和Stride表示张量排布格式，层次化表述法支持元组嵌套描述复杂内存排布如分形格式。
- [MakeLayout](make_layout.md)（`same_topic`）：Layout说明Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
- [Slice（基础API）](../tensor_structure/slice.md)（`same_topic`）：Slice（基础API） 与《Layout》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [ViewEngine](../tensor_structure/view_engine.md)（`same_topic`）：ViewEngine 与《Layout》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《Layout》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
