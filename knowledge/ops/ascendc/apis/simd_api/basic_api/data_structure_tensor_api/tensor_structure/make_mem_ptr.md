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

- [MakeTensor](make_tensor.md)（`same_topic`）：MakeMemPtr 与《MakeTensor》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Pointer（基础API）](pointer.md)（`same_topic`）：MakeMemPtr 与《Pointer（基础API）》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Tensor](tensor.md)（`same_topic`）：MakeMemPtr 与《Tensor》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [Tensor数据结构](tensor_structure.md)（`same_topic`）：MakeMemPtr 与《Tensor数据结构》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《MakeMemPtr》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [数据结构(TensorAPI，试验特性)](../data_structure_tensor_api.md)（`same_topic`）：MakeMemPtr 与《数据结构(TensorAPI，试验特性)》的实质衔接是：MakeMemPtr 先把地址、物理存储位置和类型包装成 HardwareMemPtr，再由 MakeTensor 构成 Tensor；Pointer/Tensor 结构卡定义这一适配边界。
<!-- cannbot:related:end -->
