---
type: API
title: AscAtomicExch
description: 对Global Memory中address指向的元素执行原子赋值操作，将该元素值设置为val，返回修改前的值。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_exch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicExch

对Global Memory中address指向的元素执行原子赋值操作，即将该元素值设置为val。
函数原型：int32_t asc_atomic_exch(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_exch为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AtomicExch](../../basic_api/atomic_operations/atomic_exch.md)（`related`）：基础 C++ AtomicExch 提供同一 GM 原子交换契约，可与 C Scalar 版本按语言接口选择。
- [asc_atomic_exch](../../../simt_api/atomic_operations/asc_atomic_exch.md)（`related`）：asc_atomic_exch 与《AscAtomicExch》的实质衔接是：SIMT、C scalar 与基础 API 的 AtomicExch 都实现同址原子交换；SIMT 原子简介补充返回旧值和并发顺序约束。
<!-- cannbot:related:end -->
