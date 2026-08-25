---
type: API
title: asc_atomic_min
description: 对Unified Buffer或Global Memory数据做原子求最小值操作，即将Unified Buffer或Global Memory的数据与指定数据中的最小值赋值到Unified
  Buffer或Global Memory地址中。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---

# asc_atomic_min

对Unified Buffer或Global Memory数据做原子求最小值操作，即将Unified Buffer或Global Memory的数据与指定数据中的最小值赋值到Unified Buffer或Global Memory地址中。
函数原型：int32_t asc_atomic_min(int32_t *address, int32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于依赖接口返回值判断线程先后顺序的场景，结果可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half、bfloat16_t、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscAtomicMin](../../simd_api/c_api/scalar_compute/asc_atomic_min.md)（`related`）：asc_atomic_min 与《AscAtomicMin》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
- [AscSetAtomicMin](../../simd_api/c_api/simd_atomic/asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《asc_atomic_min》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AtomicMin](../../simd_api/basic_api/atomic_operations/atomic_min.md)（`related`）：asc_atomic_min 与《AtomicMin》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
- [SetAtomicMin](../../simd_api/basic_api/atomic_operations/set_atomic_min_isasi.md)（`related`）：asc_atomic_min 与《SetAtomicMin》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
- [asc_atomic_max](asc_atomic_max.md)（`same_topic`）：asc_atomic_min 与《asc_atomic_max》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
<!-- cannbot:related:end -->
