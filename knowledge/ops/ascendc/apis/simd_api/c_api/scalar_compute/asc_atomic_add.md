---
type: API
title: AscAtomicAdd
description: 对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicAdd

对Global Memory中的数据与指定数据执行原子加操作，即将val累加到address指向的数据元素上。 将address指向的GM地址上的旧值（old_value）与输入标量值（val）求和，将和结果（new_value）写回GM地址，返回该地址修改前的值（old_value）。
函数原型：int32_t asc_atomic_add(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_add为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AtomicAdd](../../basic_api/atomic_operations/atomic_add.md)（`same_topic`）：对Global Memory中的数据与指定数据执行原子加操作，即将val累加到address指向的数据元素上。；在指定GM地址上进行原子加操作。将address指向的GM地址上的旧值与输入值进行原子加运算，将结果写回GM地址，返回修改前的旧值。两卡描述同一 GM 标量原子加契约，分别提供 C API 与 Basic API 的入口、类型和对齐边界。
<!-- cannbot:related:end -->
