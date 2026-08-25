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
