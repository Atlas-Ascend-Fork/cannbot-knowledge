---
type: API
title: LocalMemAllocator简介
description: LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/LocalMemAllocator_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# LocalMemAllocator简介

LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。

<!-- cannbot:related:start -->
## 相关

- [避免TPipe在对象内创建和初始化](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`explains`）：LocalMemAllocator 可显式管理本地内存，适合把分配生命周期移出对象反复初始化路径。
- [静态Tensor编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《LocalMemAllocator简介》说明LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [CheckLocalMemoryIA](../../debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocator简介》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [Alloc](alloc.md)（`same_topic`）：Alloc说明根据用户指定的逻辑位置、数据类型、数据长度返回对应的LocalTensor对象。
- [GetBaseAddr](../t_pipe/get_base_addr.md)（`same_topic`）：LocalMemAllocator 介绍解释逻辑位置、基础地址和偏移模型。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：GetCurAddr说明返回当前物理位置空闲的起始地址。
- [LocalMemAllocatorConstructor](local_mem_allocator_constructor.md)（`same_topic`）：LocalMemAllocatorConstructor说明LocalMemAllocator构造函数，用于初始化指定物理位置的内存分配器对象。
<!-- cannbot:related:end -->
