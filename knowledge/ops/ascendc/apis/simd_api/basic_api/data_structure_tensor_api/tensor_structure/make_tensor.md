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

- [MakeMemPtr](make_mem_ptr.md)（`related`）：“试验接口。构造带物理存储位置标记和数据类型信息的内存指针适配器 HardwareMemPtr。”产生指针适配器，而“试验接口。将内存指针（MakeMemPtr 生成）与布局对象（MakeFrameLayout/MakeLayout 生成）绑定，生成带完整类型信息的 Tensor 对象。”明确消费该结果；这是从裸地址到 Tensor 的直接两步构造链。
- [Tensor](tensor.md)（`related`）：“核心方法：GetValue/SetValue 元素级读写，GetSize 元素数，GetShapeInfo/SetShapeInfo 形状信息，GetPhyAddr 物理地址，ReinterpretCast 类型重解释，operator［］ 下标访问，Slice 子张量切取。通过 MakeTensor 构造，可直接传入 Copy/Mmad 接口，编译器根据 Engine 物理位置和 Layout 布局模式自动选择硬件指令。仅 950 支持。”说明 Tensor 对象必须由 MakeTensor 构造后才能交给 Copy/Mmad；“试验接口。将内存指针（MakeMemPtr 生成）与布局对象（MakeFrameLayout/MakeLayout 生成）绑定，生成带完整类型信息的 Tensor 对象。”给出构造所消费的指针与布局。两页闭合 Tensor 从物理地址和 Layout 到可执行对象的创建步骤。
<!-- cannbot:related:end -->
