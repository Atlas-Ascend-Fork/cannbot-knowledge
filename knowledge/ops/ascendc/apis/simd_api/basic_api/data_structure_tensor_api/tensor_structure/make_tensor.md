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
