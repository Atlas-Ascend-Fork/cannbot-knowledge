---
type: API
title: AscSetAtomicNone
description: 清空原子操作状态，与原子加、取大、取小接口配合使用，在完成原子操作后关闭原子操作。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_atomic_none.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetAtomicNone

清空原子操作的状态。一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。
函数原型：void asc_set_atomic_none()
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。；一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。。asc_set_atomic_min 开启的原子最小状态需要由 asc_set_atomic_none 清除，但 none 也服务 add 和 max，故两者是启用与清理的任务链而非单一 min 接口的同义面。
- [AscSetStoreAtomicConfigV1](asc_set_store_atomic_config_v1.md)（`related`）：约束：使用完成后，建议通过asc_set_atomic_none清空原子操作的状态，以免影响后续相关指令功能。；该指令执行前不会对GM的数据做清零操作，开发者需在需要时手动添加清零操作。；清空原子操作的状态。一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。；焦点要求使用结束后清状态，目标提供关闭动作，形成原子配置生命周期。
- [asc_set_atomic_min_int（废弃）](asc_set_atomic_min_int_deprecated.md)（`same_topic`）：约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。 清空原子操作的状态。一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。 旧接口的约束与 None 的状态清理语义共同确定原子最小完成后的收尾调用。
<!-- cannbot:related:end -->
