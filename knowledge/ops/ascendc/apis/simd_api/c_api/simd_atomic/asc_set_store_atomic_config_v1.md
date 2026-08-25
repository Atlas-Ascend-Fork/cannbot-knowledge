---
type: API
title: AscSetStoreAtomicConfigV1
description: 设置原子操作启用位与原子操作类型的值。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_store_atomic_config_v1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetStoreAtomicConfigV1

设置原子操作启用位与原子操作类型的值。
函数原型：void asc_set_store_atomic_config_v1(uint16_t type, uint16_t op)
约束：使用完成后，建议通过asc_set_atomic_none清空原子操作的状态，以免影响后续相关指令功能。；该指令执行前不会对GM的数据做清零操作，开发者需在需要时手动添加清零操作。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《AscSetStoreAtomicConfigV1》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：AscSetStoreAtomicConfigV1 打开并选择随路原子类型后，文档明确要求用 AscSetAtomicNone 清空状态，避免污染后续 GM 搬运。
- [SetStoreAtomicConfig](../../basic_api/atomic_operations/set_store_atomic_config_isasi.md)（`related`）：SetStoreAtomicConfig 与《AscSetStoreAtomicConfigV1》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
- [AscGetStoreAtomicConfig](asc_get_store_atomic_config.md)（`same_topic`）：Get 与 Set 构成配置读写闭环。
- [AscStoreAtomicConfig](../struct/asc_store_atomic_config.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《AscSetStoreAtomicConfigV1》具体提供“设置原子操作启用位与原子操作类型的值。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
<!-- cannbot:related:end -->
