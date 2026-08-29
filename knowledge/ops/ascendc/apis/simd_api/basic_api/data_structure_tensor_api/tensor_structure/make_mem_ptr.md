---
type: API
title: MakeMemPtr
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 MakeMemPtr用于构造带物理存储位置标记和数据类型信息的内存指针适配器HardwareMemPtr，支持的物理位置如下表所示。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/MakeMemPtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MakeMemPtr

试验接口。构造带物理存储位置标记和数据类型信息的内存指针适配器 HardwareMemPtr。头文件 `tensor_api/tensor.h`。三种调用形式：指定物理位置和数据类型从原始地址构造、指定物理位置从已有指针构造、从已有指针自动推导物理位置。仅 950 支持。试验接口，不保证后续兼容性。

<!-- cannbot:related:start -->
## 相关

- [MakeTensor](make_tensor.md)（`related`）：“试验接口。构造带物理存储位置标记和数据类型信息的内存指针适配器 HardwareMemPtr。”产生指针适配器，而“试验接口。将内存指针（MakeMemPtr 生成）与布局对象（MakeFrameLayout/MakeLayout 生成）绑定，生成带完整类型信息的 Tensor 对象。”明确消费该结果；这是从裸地址到 Tensor 的直接两步构造链。
<!-- cannbot:related:end -->
