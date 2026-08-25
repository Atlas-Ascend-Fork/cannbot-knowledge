---
type: API
title: AscAtomicMin
description: 对Global Memory中的数据执行原子求最小值操作，将address指向的数据元素与val中的最小值写回该地址。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicMin

对Global Memory中的数据与指定数据执行原子求最小值操作，即将address指向的数据元素与val中的最小值写回到该地址。
函数原型：int32_t asc_atomic_min(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_min为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](../simd_atomic/asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《AscAtomicMin》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AtomicMin](../../basic_api/atomic_operations/atomic_min.md)（`related`）：基础 AtomicMin 与 C Scalar AscAtomicMin 都在 GM 做原子取小并返回旧值；目标卡补充模板 dtype 范围，focal 补充 DCache 一致性和 MTE 手工同步要求。
- [asc_atomic_min](../../../simt_api/atomic_operations/asc_atomic_min.md)（`related`）：asc_atomic_min 与《AscAtomicMin》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
<!-- cannbot:related:end -->
