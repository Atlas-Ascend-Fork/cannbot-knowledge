---
type: API
title: Tensor数据结构
description: TensorAPI Tensor 数据结构集，包含 Tensor、Pointer、ViewEngine 及 MakeTensor、Slice 等相关接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/tensor_structure.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Tensor数据结构

TensorAPI 中描述张量对象的 Tensor 数据结构集合。包含 Tensor、Pointer、ViewEngine 三类基础结构，以及 MakeTensor、MakeMemPtr、Slice 等构造与切片接口。Tensor 与 Layout 配合使用，提供对缓冲区数据的视图化访问能力，属试验特性。

<!-- cannbot:related:start -->
## 相关

- [Layout数据结构](../layout_structure/layout_structure.md)（`related`）：Layout 提供 shape/stride 寻址，是 Tensor 的布局部分。
- [Slice（基础API）](slice.md)（`related`）：Slice 从 Tensor 生成共享存储的子视图，继承 Pointer 生命周期。
- [MakeMemPtr](make_mem_ptr.md)（`same_topic`）：MakeMemPtr 与《Tensor数据结构》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [MakeTensor](make_tensor.md)（`same_topic`）：MakeTensor 从 Pointer 与 Layout 构造 Tensor，是结构总览的核心创建入口。
- [Pointer（基础API）](pointer.md)（`same_topic`）：Tensor 结构总页解释 pointer、layout 和 engine 如何组成 Tensor。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《Tensor数据结构》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
