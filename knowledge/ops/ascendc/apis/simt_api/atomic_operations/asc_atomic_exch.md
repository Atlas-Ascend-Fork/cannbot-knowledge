---
type: API
title: asc_atomic_exch
description: 对Unified Buffer或Global Memory地址做原子赋值操作，即将指定数据赋值到Unified Buffer或Global
  Memory地址中。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_exch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_exch

对Unified Buffer或Global Memory地址做原子赋值操作，即将指定数据赋值到Unified Buffer或Global Memory地址中。
函数原型：float asc_atomic_exch(float *address, float val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。当多个线程向同一地址写入不同值时，最终保留的值取决于原子操作的串行化顺序，可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscAtomicExch](../../simd_api/c_api/scalar_compute/asc_atomic_exch.md)（`related`）：asc_atomic_exch 与《AscAtomicExch》的实质衔接是：SIMT、C scalar 与基础 API 的 AtomicExch 都实现同址原子交换；SIMT 原子简介补充返回旧值和并发顺序约束。
- [AtomicExch](../../simd_api/basic_api/atomic_operations/atomic_exch.md)（`same_topic`）：《AtomicExch》处理“对GM地址执行原子交换，将输入标量值写入并返回修改前的旧值。”。《asc_atomic_exch》明确“对Unified Buffer或Global Memory地址做原子赋值操作，即将指定数据赋值到Unified Buffer或Global Memory地址中。”，可直接用于核对AtomicExch 的 C/C++ 入口及与 AtomicCas 的原子更新语义差异。
- [原子操作简介](atomic_operations_intro.md)（`same_topic`）：asc_atomic_exch 与《原子操作简介》的实质衔接是：SIMT、C scalar 与基础 API 的 AtomicExch 都实现同址原子交换；SIMT 原子简介补充返回旧值和并发顺序约束。
<!-- cannbot:related:end -->
