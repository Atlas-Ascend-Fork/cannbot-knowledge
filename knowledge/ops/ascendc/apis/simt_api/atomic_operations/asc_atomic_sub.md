---
type: API
title: asc_atomic_sub
description: 对Unified Buffer或Global Memory上的数据与指定数据执行原子减操作，即在这些内存区域的数据中减去指定数据。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_sub

对Unified Buffer或Global Memory上的数据与指定数据执行原子减操作，即在这些内存区域的数据中减去指定数据。
函数原型：int32_t asc_atomic_sub(int32_t *address, int32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于浮点累减或依赖返回值顺序敏感的场景，结果可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [asc_atomic_add](asc_atomic_add.md)（`related`）：AscAtomicAdd 是同一 SIMT 地址与返回旧值模型下的加法对偶，可据更新方向选择且共享并发顺序不确定性。
- [AscAtomicSub](../../simd_api/c_api/scalar_compute/asc_atomic_sub.md)（`same_topic`）：AscAtomicSub 与《asc_atomic_sub》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
<!-- cannbot:related:end -->
