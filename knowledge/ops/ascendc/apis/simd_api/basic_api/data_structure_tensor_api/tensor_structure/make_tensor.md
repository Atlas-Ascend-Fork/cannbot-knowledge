---
type: API
title: MakeTensor
description: 将内存指针与布局对象绑定生成带完整类型信息的Tensor对象，根据物理位置自动推导返回GlobalTensor或LocalTensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/MakeTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MakeTensor

试验接口。将内存指针（MakeMemPtr 生成）与布局对象（MakeFrameLayout/MakeLayout 生成）绑定，生成带完整类型信息的 Tensor 对象。根据指针物理位置自动推导返回 GlobalTensor（GM）或 LocalTensor（Local Memory）。生成的 Tensor 可直接传入 Copy/Mmad 接口，编译器根据 Engine 物理位置和 Layout 布局模式自动选择硬件指令。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [CopyGmToL1](../../cube_compute_tensor_api/cube_compute_load/copy_gm_to_l1.md)（`related`）：CopyGmToL1 依赖带 Engine 物理位置和 Layout 的 Tensor 参数来推导 GM→L1 搬运形态；MakeTensor 正是把 HardwareMemPtr 与 Layout 绑定为可传给 Copy 的 Tensor。
- [MakeLayout](../layout_structure/make_layout.md)（`related`）：MakeTensor 的第二项必需输入是 MakeLayout 生成的 Shape/Stride 布局；编译器联合该布局与 MemPtr Engine 选择 Copy/Mmad 指令。
- [Pointer（基础API）](pointer.md)（`related`）：MakeTensor 消费 Pointer 与 Layout 形成可索引 Tensor。
- [Tensor](tensor.md)（`related`）：Tensor 卡定义 Engine 与 Layout 绑定后的对象语义，MakeTensor 给出从 HardwareMemPtr 和 Layout 实际构造 GlobalTensor/LocalTensor 的入口。
- [数据结构(TensorAPI，试验特性)](../data_structure_tensor_api.md)（`related`）：MakeTensor 把 Pointer 与 Layout 组合成 Tensor，是从本总览的数据结构模型进入可用张量对象的构造契约。
- [MakeMemPtr](make_mem_ptr.md)（`same_topic`）：MakeMemPtr 与《MakeTensor》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Slice（基础API）](slice.md)（`same_topic`）：Slice（基础API） 与《MakeTensor》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [Tensor数据结构](tensor_structure.md)（`same_topic`）：MakeTensor 从 Pointer 与 Layout 构造 Tensor，是结构总览的核心创建入口。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《MakeTensor》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
