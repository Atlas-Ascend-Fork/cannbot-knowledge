---
type: API
title: AscAtomicSub
description: 对Global Memory中的数据执行原子减操作，将val从address指向的数据元素上减去，返回修改前的值。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicSub

对Global Memory中的数据与指定数据执行原子减操作，即将val从address指向的数据元素上减去。
函数原型：int32_t asc_atomic_sub(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_sub为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscDcci](../cache_ctrl/asc_dcci.md)（`related`）：AscAtomicSub 与《AscDcci》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [ReadGmByPassDCache](../../basic_api/scalar_compute/read_gm_by_pass_d_cache_isasi.md)（`related`）：AscAtomicSub 与《ReadGmByPassDCache》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [WriteGmByPassDCache](../../basic_api/scalar_compute/write_gm_by_pass_d_cache_isasi.md)（`related`）：AscAtomicSub 与《WriteGmByPassDCache》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [AscAtomicAdd](asc_atomic_add.md)（`same_topic`）：AscAtomicSub 与《AscAtomicAdd》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [asc_atomic_sub](../../../simt_api/atomic_operations/asc_atomic_sub.md)（`same_topic`）：AscAtomicSub 与《asc_atomic_sub》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
<!-- cannbot:related:end -->
