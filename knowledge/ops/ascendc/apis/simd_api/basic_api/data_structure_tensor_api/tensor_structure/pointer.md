---
type: API
title: Pointer（基础API）
description: Pointer定义指针迭代器，用于遍历和访问张量数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/Pointer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Pointer（基础API）

Pointer定义指针迭代器，用于遍历和访问张量数据。

# Pointer（基础API）

Pointer定义指针迭代器，用于遍历和访问张量数据。

本接口属于 Tensor 数据结构操作接口，用于描述和操作张量的布局与结构。

参数说明：ptr：T* 指向数据的指针。；position：P 指针的位置信息。

约束：ptr指针必须指向有效的内存空间。；position必须正确描述指针的当前位置。；Pointer支持多种内存空间的指针类型。

本接口为 Ascend C 算子开发 API，具体使用方法和约束请参考官方文档。

<!-- cannbot:related:start -->
## 相关

- [MakeTensor](make_tensor.md)（`related`）：MakeTensor 消费 Pointer 与 Layout 形成可索引 Tensor。
- [Slice（基础API）](slice.md)（`related`）：Slice 基于 Pointer 偏移生成子视图，地址空间和生命周期仍继承原指针。
- [MakeMemPtr](make_mem_ptr.md)（`same_topic`）：MakeMemPtr 与《Pointer（基础API）》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Tensor数据结构](tensor_structure.md)（`same_topic`）：Tensor 结构总页解释 pointer、layout 和 engine 如何组成 Tensor。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《Pointer（基础API）》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
