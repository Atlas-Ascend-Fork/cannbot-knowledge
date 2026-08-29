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

- [SIMT实现InsertHashTable算子案例](../../../../guides/operator_practice/best_practices/simt_insert_hash_table.md)（`explains`）：案例卡说明“线程通过原子指令asc_atomic_cas修改flag来获取桶的写权限。”；接口卡给出“如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”，该 compare-and-swap 语义正是开放寻址插入时竞争桶所有权的实现原语。
- [asc_atomic_cas](../../../simt_api/atomic_operations/asc_atomic_cas.md)（`same_topic`）：对Global Memory中address指向的元素执行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。；对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。两卡定义同一 compare-and-swap 决策，分别给出 Scalar C API 的缓存同步合同与 SIMT 的线程竞争合同。
<!-- cannbot:related:end -->
