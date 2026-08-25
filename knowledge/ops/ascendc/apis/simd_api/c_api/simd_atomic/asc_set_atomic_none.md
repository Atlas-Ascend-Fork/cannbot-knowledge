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

- [AscSetAtomicAdd](asc_set_atomic_add.md)（`related`）：AscSetAtomicAdd 开启后会影响后续 GM 搬运，AscSetAtomicNone 是文档要求的状态清理动作，二者构成成对的启用/复位协议。
- [AscSetAtomicMax](asc_set_atomic_max.md)（`related`）：AscSetAtomicMax 会影响后续 UB/L0C/L1→GM 写回，完成目标原子区间后必须用 AscSetAtomicNone 恢复非原子状态。
- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《AscSetAtomicNone》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AscSetStoreAtomicConfigV1](asc_set_store_atomic_config_v1.md)（`related`）：AscSetStoreAtomicConfigV1 打开并选择随路原子类型后，文档明确要求用 AscSetAtomicNone 清空状态，避免污染后续 GM 搬运。
- [SetAtomicMax](../../basic_api/atomic_operations/set_atomic_max_isasi.md)（`related`）：SetAtomicMax 与《AscSetAtomicNone》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [asc_set_atomic_add_int（废弃）](../deprecated_interface/asc_set_atomic_add_int_deprecated.md)（`related`）：设置原子加状态后需用 asc_set_atomic_none 关闭原子模式，避免后续搬运继续累加。
- [asc_set_atomic_min_int（废弃）](asc_set_atomic_min_int_deprecated.md)（`related`）：原子取小状态会影响后续搬运，完成目标区间后需 AscSetAtomicNone 清理，避免污染无关写回。
<!-- cannbot:related:end -->
