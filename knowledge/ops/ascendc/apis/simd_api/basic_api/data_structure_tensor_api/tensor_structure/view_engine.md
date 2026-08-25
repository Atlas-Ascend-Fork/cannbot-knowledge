---
type: API
title: ViewEngine
description: ViewEngine是Tensor API中的视图引擎，负责持有一个指针对象Iterator，通过Begin()返回这段视图的起始位置。在LocalTensor中，ViewEngine和Layout一起组成一个Tensor的视图。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/ViewEngine.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# ViewEngine

Tensor API 中的视图引擎，持有指针对象 Iterator，通过 Begin() 返回视图起始位置。在 LocalTensor 中，ViewEngine 与 Layout 组成 Tensor 的视图。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [GetShape](../layout_structure/get_shape.md)（`same_topic`）：ViewEngine 与《GetShape》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [GetStride](../layout_structure/get_stride.md)（`same_topic`）：ViewEngine 与《GetStride》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Layout](../layout_structure/layout.md)（`same_topic`）：ViewEngine 与《Layout》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Layout数据结构](../layout_structure/layout_structure.md)（`same_topic`）：ViewEngine 与《Layout数据结构》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [MakeMemPtr](make_mem_ptr.md)（`same_topic`）：ViewEngine 与《MakeMemPtr》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [MakeTensor](make_tensor.md)（`same_topic`）：ViewEngine 与《MakeTensor》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Pointer（基础API）](pointer.md)（`same_topic`）：ViewEngine 与《Pointer（基础API）》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Slice（基础API）](slice.md)（`same_topic`）：ViewEngine 与《Slice（基础API）》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Tensor](tensor.md)（`same_topic`）：ViewEngine 与《Tensor》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [Tensor数据结构](tensor_structure.md)（`same_topic`）：ViewEngine 与《Tensor数据结构》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [数据结构(TensorAPI，试验特性)](../data_structure_tensor_api.md)（`same_topic`）：ViewEngine 与《数据结构(TensorAPI，试验特性)》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
