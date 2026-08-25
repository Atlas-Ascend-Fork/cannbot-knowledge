---
type: API
title: 数据结构(TensorAPI，试验特性)
description: TensorAPI（试验特性）数据结构总览，涵盖内置数据类型、Layout 与 Tensor 相关数据结构及工具接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/data_structure_TensorAPI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据结构(TensorAPI，试验特性)

TensorAPI（试验特性）数据结构总览，提供基于 Layout 与 Tensor 抽象的层次化张量编程模型。包含内置数据类型与精度转换；Layout 侧提供 Layout、Shape、Stride、Coord 及构造/查询接口（MakeLayout、GetShape 等）；Tensor 侧提供 Tensor、Pointer、ViewEngine 及 MakeTensor、Slice 等接口；GetLayoutPattern 为工具接口。属试验特性，接口可能随版本调整。

<!-- cannbot:related:start -->
## 相关

- [GetShape](layout_structure/get_shape.md)（`related`）：GetShape 从 TensorAPI Layout 取出层次 shape，可用于验证 MakeTensor 前后的布局契约。
- [MakeTensor](tensor_structure/make_tensor.md)（`related`）：MakeTensor 把 Pointer 与 Layout 组合成 Tensor，是从本总览的数据结构模型进入可用张量对象的构造契约。
- [Tensor](tensor_structure/tensor.md)（`related`）：Tensor 对象承载总览所述 Layout、Pointer 与 ViewEngine 语义，是后续 Slice/访问操作的统一载体。
- [MakeMemPtr](tensor_structure/make_mem_ptr.md)（`same_topic`）：MakeMemPtr 与《数据结构(TensorAPI，试验特性)》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [ViewEngine](tensor_structure/view_engine.md)（`same_topic`）：ViewEngine 与《数据结构(TensorAPI，试验特性)》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
