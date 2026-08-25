---
type: API
title: asc_atomic_cas
description: 对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_cas.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_cas

对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
函数原型：float asc_atomic_cas(float *address, float compare, float val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。使用asc_atomic_cas实现抢占逻辑时，可保证最多一个线程抢占成功，但不保证固定由哪个线程抢占成功。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT实现InsertHashTable算子案例](../../../guides/operator_practice/best_practices/simt_insert_hash_table.md)（`explains`）：哈希表插入指南的抢占槽位逻辑依赖 compare-and-swap；asc_atomic_cas 给出“地址等于 compare 才写 val”及最多一个线程成功的原子契约。
- [AscAtomicCas](../../simd_api/c_api/scalar_compute/asc_atomic_cas.md)（`same_topic`）：asc_atomic_cas说明对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
- [AtomicCas](../../simd_api/basic_api/atomic_operations/atomic_cas.md)（`same_topic`）：C++ AtomicCas 与 SIMT asc_atomic_cas 提供同一 CAS 原语，可据 Kernel 编程模型选择。
<!-- cannbot:related:end -->
