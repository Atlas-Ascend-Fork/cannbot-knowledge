---
type: API
title: Coord（基础API）
description: 定义张量逻辑坐标，并配合 Layout 完成多维坐标到线性内存索引的映射。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Coord.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Coord（基础API）

Coord 用于定义张量的逻辑坐标，配合 Layout 实现逻辑坐标到一维内存地址的映射。头文件为 tensor_api/tensor.h。
Coord 通过 Std::tuple 的可变参数模板 Coords 定义各维度坐标，需使用 MakeCoord 构造实例。
作为参数传入 Layout 的 operator() 成员函数可完成坐标到索引的映射，传入 Tensor 的 Slice 接口可实现张量偏移与切片。
还可通过 Crd2Idx 接口将多维坐标转换为线性坐标。本接口为试验接口，后续版本可能调整，不保证兼容性。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Coordinate](../../aux_data_structures/coordinate/coordinate.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Coordinate正文说明“Coordinate 辅助数据结构用于描述张量坐标，提供 MakeCoord 构造与 Crd2Idx 坐标到索引转换接口”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Crd2Idx](../../aux_data_structures/coordinate/crd2_idx.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Crd2Idx正文说明“将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [MakeCoord](../../aux_data_structures/coordinate/make_coord.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；MakeCoord正文说明“将传入的数据打包成Coord数据结构”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout](layout.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout正文说明“Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout和层次化表述法正文说明“Layout通过Shape和Stride表示张量排布格式，层次化表述法支持元组嵌套描述复杂内存排布如分形格式”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout数据结构](layout_structure.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout数据结构正文说明“TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [MakeCoord](make_coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；MakeCoord正文说明“需要包含的头文件为：#include "tensor_api/tensor.h"。 构造Coord对象，用于定义张量的坐标”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Slice（基础API）](../tensor_structure/slice.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Slice（基础API）正文说明“需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
<!-- cannbot:related:end -->
