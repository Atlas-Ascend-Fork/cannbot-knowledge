---
type: API
title: AscAtomicOr
description: 对Global Memory中的数据执行原子按位或操作，将val按位或到address指向的数据元素上。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_or.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicOr

对Global Memory中的数据与指定数据执行原子或操作，即将val按位或到address指向的数据元素上。
函数原型：int32_t asc_atomic_or(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_or为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscAtomicAnd](asc_atomic_and.md)（`related`）：AtomicAnd 与 AtomicOr 共享原子地址/返回值约束，但位合并语义不同，适用于清位与置位的决策。
- [AscAtomicCas](asc_atomic_cas.md)（`related`）：CAS 可实现带条件的复合状态更新，而 AtomicOr 只做无条件置位；需要条件更新时应切换契约。
- [asc_atomic_or](../../../simt_api/atomic_operations/asc_atomic_or.md)（`same_topic`）：SIMT 与 C SIMD 标量接口都对 GM 地址执行原子按位或；对照可按线程模型选择调用入口。
<!-- cannbot:related:end -->
