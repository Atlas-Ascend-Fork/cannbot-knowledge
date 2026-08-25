---
type: API
title: Tensor
description: 将内存访问引擎Engine与布局Layout绑定，分为GlobalTensor和LocalTensor两种，公共接口由BaseTensor提供。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/Tensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Tensor

试验接口。Tensor 将内存访问引擎 Engine（描述物理存储位置和访问方式）与 Layout（描述形状和布局）绑定。分 GlobalTensor（Global Memory 外部存储）和 LocalTensor（AI Core Local Memory 内部存储），公共接口由 BaseTensor<TensorAttribute<EngineType, LayoutType>> 提供。头文件 `tensor_api/tensor.h`。

核心方法：GetValue/SetValue 元素级读写，GetSize 元素数，GetShapeInfo/SetShapeInfo 形状信息，GetPhyAddr 物理地址，ReinterpretCast 类型重解释，operator[] 下标访问，Slice 子张量切取。通过 MakeTensor 构造，可直接传入 Copy/Mmad 接口，编译器根据 Engine 物理位置和 Layout 布局模式自动选择硬件指令。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Layout](../layout_structure/layout.md)（`related`）：Tensor 的地址映射由内含 Layout 的 Shape/Stride 决定；Layout 卡提供 Capacity、Size、Rank 及层次化分形表达，直接解释 Tensor 如何定位元素。
- [MakeTensor](make_tensor.md)（`related`）：Tensor 卡定义 Engine 与 Layout 绑定后的对象语义，MakeTensor 给出从 HardwareMemPtr 和 Layout 实际构造 GlobalTensor/LocalTensor 的入口。
- [数据结构(TensorAPI，试验特性)](../data_structure_tensor_api.md)（`related`）：Tensor 对象承载总览所述 Layout、Pointer 与 ViewEngine 语义，是后续 Slice/访问操作的统一载体。
- [MakeMemPtr](make_mem_ptr.md)（`same_topic`）：MakeMemPtr 与《Tensor》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Slice（基础API）](slice.md)（`same_topic`）：Slice（基础API） 与《Tensor》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《Tensor》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
