---
type: API
title: asc_atomic_dec
description: 对Unified Buffer或Global Memory上address的数值进行原子减1操作，如果address上的数值等于0或大于指定数值val，则对address赋值为val，否则将address上数值减1。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_dec.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_dec

对Unified Buffer或Global Memory上address的数值进行原子减1操作，如果address上的数值等于0或大于指定数值val，则对address赋值为val，否则将address上数值减1。
函数原型：uint32_t asc_atomic_dec(uint32_t *address, uint32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于依赖返回值分配序号或槽位的场景，返回值对应的序号唯一，但分配给具体线程的顺序可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即uint32_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [asc_atomic_inc](asc_atomic_inc.md)（`related`）：AtomicInc 在达到 val 时回绕到 0，AtomicDec 在 0/越界时回绕到 val；二者是循环计数器的增减方向选择。
- [AscAtomicDec](../../simd_api/c_api/scalar_compute/asc_atomic_dec.md)（`same_topic`）：AscAtomicDec：AscAtomicDec与SIMT asc_atomic_dec执行同一GM原子自减，AscAtomicInc提供相反更新的边界对照，便于验证返回值和上下界行为。 目标卡《asc_atomic_dec》补充：对Unified Buffer或Global Memory上address的数值进行原子减1操作，如果address上的数值等于0或大于指定数值val，则对address赋值为val，否则将address上数值减1。
<!-- cannbot:related:end -->
