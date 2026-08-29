---
type: API
title: asc_atomic_or
description: 对Unified Buffer或Global Memory上address的数值与指定数值val进行原子或（ ）操作，即将address数值或（
  ）val的结果赋值到Unified Buffer或Global Memory上。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_or.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_or

对Unified Buffer或Global Memory上address的数值与指定数值val进行原子或（|）操作，即将address数值或（|）val的结果赋值到Unified Buffer或Global Memory上。
函数原型：int32_t asc_atomic_or(int32_t *address, int32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于依赖接口返回值判断线程先后顺序的场景，结果可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [TopK 950 Direct Invoke 算子知识](../../../operators/direct/math/math/top_k_950.md)（`related`）：“对Unified Buffer或Global Memory上address的数值与指定数值val进行原子或（｜）操作，即将address数值或（｜）val的结果赋值到Unified Buffer或Global Memory上。”与“if (static_cast<int64_t>(narrowed) != value) asc_atomic_or(rangeFlag, 1U);”提供双方正文证据。TopK 的 int64 窄化检测在任一值不可表示时以 asc_atomic_or 原子置位共享 rangeFlag，API 卡给出该原子读改写合同，直接支撑多线程范围标记。
- [AscAtomicOr](../../simd_api/c_api/scalar_compute/asc_atomic_or.md)（`same_topic`）：对Global Memory中的数据与指定数据执行原子或操作，即将val按位或到address指向的数据元素上。；对Unified Buffer或Global Memory上address的数值与指定数值val进行原子或（｜）操作，即将address数值或（｜）val的结果赋值到Unified Buffer或Global Memory上。。两接口都实现 asc_atomic_or 的原子读改写；Scalar C API 仅操作 GM 且强调流水/DCache 同步，SIMT API 还允许 UB 并受线程调度语义约束。
<!-- cannbot:related:end -->
