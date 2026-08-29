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

- [AscDcci](../cache_ctrl/asc_dcci.md)（`related`）：原子交换接口明确“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；缓存接口解释“Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。”，给出交换前后插入 DCCI 的一致性原因。
- [AtomicExch](../../basic_api/atomic_operations/atomic_exch.md)（`same_topic`）：在指定GM地址上进行原子交换操作。将address指向的GM地址上的旧值与输入值进行原子交换运算，将结果写回GM地址，返回修改前的旧值。仅Ascend 950PR/950DT支持。；对Global Memory中address指向的元素执行原子赋值操作，即将该元素值设置为val。两页描述同一 GM 原子交换语义，C scalar 页进一步给出流水同步与 DCache 一致性约束，能直接支撑接口选型和正确使用。
<!-- cannbot:related:end -->
