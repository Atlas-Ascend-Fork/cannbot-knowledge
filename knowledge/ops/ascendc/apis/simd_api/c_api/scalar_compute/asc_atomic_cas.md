---
type: API
title: AscAtomicCas
description: 对Global Memory中address指向的元素执行原子比较赋值操作，若当前值等于compare则赋值为val，否则不变。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_cas.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicCas

对Global Memory中address指向的元素执行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
函数原型：int32_t  asc_atomic_cas(__gm__ int32_t  *address, int32_t  compare, int32_t  val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_cas为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT实现InsertHashTable算子案例](../../../../guides/operator_practice/best_practices/simt_insert_hash_table.md)（`explains`）：SIMT实现InsertHashTable算子案例说明本案例介绍InsertHashTable算子，展示基于SIMT实现的大规模线程并发访问Global Memory内存的算子实践。
- [原子操作（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：原子操作（AI Core SIMT编程）说明SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能出现数据竞争，导致最终结果不符合预期。
- [AscAtomicOr](asc_atomic_or.md)（`related`）：CAS 可实现带条件的复合状态更新，而 AtomicOr 只做无条件置位；需要条件更新时应切换契约。
- [AtomicCas](../../basic_api/atomic_operations/atomic_cas.md)（`same_topic`）：AtomicCas说明对GM地址执行原子比较交换：旧值与value1相等时写入value2，否则不变，返回旧值。
- [asc_atomic_cas](../../../simt_api/atomic_operations/asc_atomic_cas.md)（`same_topic`）：asc_atomic_cas说明对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
<!-- cannbot:related:end -->
