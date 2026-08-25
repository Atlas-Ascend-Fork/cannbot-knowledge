---
type: API
title: LocalMemAllocator
description: LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/LocalMemAllocator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalMemAllocator

LocalMemAllocator 接口集合，提供 local memory 的动态分配能力。通过构造函数创建分配器实例，Alloc 按指定大小分配内存并返回地址，GetCurAddr 查询当前分配位置。适用于运行时才能确定内存需求的场景，相比 TBuf/TQue 的静态分配更灵活，但需自行管理分配与释放。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《LocalMemAllocator》说明LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [静态Tensor编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《LocalMemAllocator》说明LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [CheckLocalMemoryIA](../../debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《LocalMemAllocator》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
<!-- cannbot:related:end -->
