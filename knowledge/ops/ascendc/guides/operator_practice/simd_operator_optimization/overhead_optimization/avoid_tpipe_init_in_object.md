---
type: Guide
title: 避免TPipe在对象内创建和初始化
description: 【编译器背景知识】创建类对象时，会分配内存空间，用于存储类中的相关成员变量或函数。当类中变量需要参与计算时，变量值从内存被加载到寄存器，计算完成后，变量从寄存器存储回内存。Scalar常量折叠和常量传播是编译器编译时的优化方式，优化前编译器会判断变量是否只初始化过一次或只赋值过一次，若满足此编译优化的前提条件，变量值将会尽量驻留在寄存器中，从而在后续使用变量时，将减少读取内存的操作，提升运行性能。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 避免TPipe在对象内创建和初始化

【优先级】中
【编译器背景知识】创建类对象时，会分配内存空间，用于存储类中的相关成员变量或函数。当类中变量需要参与计算时，变量值从内存被加载到寄存器，计算完成后，变量从寄存器存储回内存。Scalar常量折叠和常量传播是编译器编译时的优化方式，优化前编译器会判断变量是否只初始化过一次或只赋值过一次，若满足此编译优化的前提条件，变量值将会尽量驻留在寄存器中，从而在后续使用变量时，将减少读取内存的操作，提升运行性能。
【描述】TPipe是用来管理全局内存和同步的框架，用户可以调用TPipe的接口，为TQue/TBuf进行内存分配。在编写Ascend C算子过程中，经常用一个类存放计算所需的相关变量，这里称类名为KernelExample。当TPipe对象在KernelExample类的实现中定义并初始化时，TPipe对象的内存空间在整个KernelExample对象的内存空间之中；需要注意的是，创建TPipe对象时，对象初始化会设置全局变量的TPipe指针，这导致KernelExample对象的内存有被外部污染的风险，此时编译器的编译优化将采取保守策略，不会对KernelExample对象中的Scalar变量进行常量折叠和常量传播。因此，在任何场景下，我们都建议将TPipe对象创建于KernelExample类外部，使得TPipe对象的内存空间独立于KernelExample类对象的内存空间，触发编译器对KernelExample类内Scalar的编译优化，减少算子Scalar指令耗时。
【反例】
代码中TPipe对象由KernelExample类内部创建并初始化，影响编译器Scalar折叠优化，在NPU侧导致Scalar不必要的增加。
【正例】
改为由Kernel入口函数创建TPipe对象，在KernelExample类中保存TPipe指针使用。
【性能对比】
通过性能数据对比可以看出，Scalar优化效果显著，平均时间从281us减少到236us，下降17%；平均scalar_time时延占比从21%下降到17%。因此在Scalar bound（达到上限）的场景下可以使用此优化措施。

<!-- cannbot:related:start -->
## 相关

- [DestroyWithoutPipeAll](../../../../apis/simd_api/basic_api/resource_management/t_pipe/destroy_without_pipe_all.md)（`explains`）：DestroyWithoutPipeAll 与《避免TPipe在对象内创建和初始化》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [LocalMemAllocator简介](../../../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator_intro.md)（`explains`）：LocalMemAllocator 可显式管理本地内存，适合把分配生命周期移出对象反复初始化路径。
- [TBufPool简介](../../../../apis/simd_api/basic_api/resource_management/t_buf_pool/t_buf_pool_intro.md)（`explains`）：TBufPool简介 与《避免TPipe在对象内创建和初始化》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe简介](../../../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe_intro.md)（`explains`）：TPipe 介绍说明对象初始化会申请/管理同步资源和本地内存，解释把它放进频繁构造对象为何增加开销。
- [507035 — 三队列 float32 tile 超 UB](../../../../runbooks/compilation/507035_float32_tile_ub.md)（`related`）：把 TPipe/多队列移出对象前仍需核算 UB；该卡提供 InitBuffer 累加定位 UB 超限的方法。
- [核函数内删除Workspace相关冗余操作](remove_workspace_redundancy.md)（`related`）：移除冗余 workspace 与避免重复 TPipe 初始化都减少固定控制/分配开销，可在同一 overhead profile 验证。
- [静态Tensor编程](../../../programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《避免TPipe在对象内创建和初始化》说明【编译器背景知识】创建类对象时，会分配内存空间，用于存储类中的相关成员变量或函数。当类中变量需要参与计算时，变量值从内存被加载到寄存器，计算完成后，变量从寄存器存储回内存。Scalar常量折叠和常量传播是编译器编译时的优化方式，优化前编译器会判断变量是否只初始化过一次或只赋值过一次，若满足此编译优化的前提条件，变量值将会尽量驻留在寄存器中，从而在后续使用变量时，将减少读取内存的操作，提升运行性能。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
<!-- cannbot:related:end -->
