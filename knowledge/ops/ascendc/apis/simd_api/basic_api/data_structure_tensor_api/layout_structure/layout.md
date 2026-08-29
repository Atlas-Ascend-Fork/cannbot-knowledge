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

- [Coord（基础API）](coord.md)（`related`）：“Coord 用于定义张量的逻辑坐标，配合 Layout 实现逻辑坐标到一维内存地址的映射。头文件为 tensor_api/tensor.h。”与“试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。”提供双方正文证据。Coord 提供逻辑坐标，Layout 依据 Shape 和 Stride 将该坐标映射为一维地址，二者是同一 tensor layout operator() 调用的输入与映射器。
- [GetShape](get_shape.md)（`related`）：“从 Layout 中提取 Shape 部分。不指定模板参数返回完整 Shape 元组；指定 Is... 从顶层 tuple 选择对应索引元素，单个索引返回该元素，多个索引返回新 tuple。头文件 `tensor_api/tensor.h`。仅 950 支持。”与“试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。”提供双方正文证据。GetShape 从 Layout 模板对象抽取其 Shape 组成，Layout 卡界定 Shape 与 Stride 如何共同描述地址映射；二者属于同一次布局检查的对象与访问器。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`same_topic`）：“试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。”与“Layout 用 Shape 和 Stride 表示张量排布：行优先 Shape(2,4) Stride(4,1)，列优先 Shape(2,4) Stride(1,2)。层次化表述法允许 Shape/Stride 元素为元组，描述内外层嵌套矩阵，如 Shape((2,3),(2,4)) Stride((1,4),(2,12))。”是双方正文中的具体合同。Layout 卡定义 Shape/Stride 地址映射对象，层次化卡用嵌套元组展开同一对象的分形表示，能推进 NZ/Zz/Zn 布局的构造理解。
<!-- cannbot:related:end -->
