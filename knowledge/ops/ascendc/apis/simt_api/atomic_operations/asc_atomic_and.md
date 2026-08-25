---
type: API
title: asc_atomic_and
description: 对Unified Buffer或Global Memory上address的数值与指定数值val进行原子与（&）操作，即将address数值与（&）val的结果赋值到Unified
  Buffer或Global Memory上。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_and.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_and

对Unified Buffer或Global Memory上address的数值与指定数值val进行原子与（&）操作，即将address数值与（&）val的结果赋值到Unified Buffer或Global Memory上。
函数原型：int32_t asc_atomic_and(int32_t *address, int32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于依赖接口返回值判断线程先后顺序的场景，结果可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscAtomicAnd](../../simd_api/c_api/scalar_compute/asc_atomic_and.md)（`related`）：asc_atomic_and 与《AscAtomicAnd》的实质衔接是：atomic AND 与其他 SIMT 原子读改写及 atomic store 配置共享并发更新契约。
- [原子操作简介](atomic_operations_intro.md)（`same_topic`）：asc_atomic_and 与《原子操作简介》的实质衔接是：atomic AND 与其他 SIMT 原子读改写及 atomic store 配置共享并发更新契约。
<!-- cannbot:related:end -->
