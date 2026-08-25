---
type: API
title: LocalMemAllocatorConstructor
description: LocalMemAllocator构造函数，用于初始化指定物理位置的内存分配器对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/LocalMemAllocator_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# LocalMemAllocatorConstructor

头文件路径为："basic_api/kernel_tensor.h"。

LocalMemAllocator构造函数。

约束：同一个物理位置的LocalMemAllocator对象，在算子生命周期内只能存在1个。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core 支持。

<!-- cannbot:related:start -->
## 相关

- [Alloc](alloc.md)（`related`）：Alloc 前必须以物理位置和起始地址构造 LocalMemAllocator；构造状态决定后续 LocalTensor 的实际地址域。
- [CheckLocalMemoryIA](../../debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocatorConstructor》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [GetCurAddr](get_cur_addr.md)（`related`）：构造后的起始地址以及每次 Alloc 后的下一空闲地址都可由 GetCurAddr 核验。
- [LocalTensor构造函数](../../data_structures/local_tensor/local_tensor_constructor.md)（`related`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《LocalMemAllocatorConstructor》明确“LocalMemAllocator构造函数，用于初始化指定物理位置的内存分配器对象。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [LocalMemAllocator简介](local_mem_allocator_intro.md)（`same_topic`）：LocalMemAllocatorConstructor说明LocalMemAllocator构造函数，用于初始化指定物理位置的内存分配器对象。
<!-- cannbot:related:end -->
