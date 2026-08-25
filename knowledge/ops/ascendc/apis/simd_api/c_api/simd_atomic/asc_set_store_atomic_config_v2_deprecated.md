---
type: API
title: asc_set_store_atomic_config_v2（废弃）
description: 该接口已废弃。原子加操作请使用asc_atomic_add实现。 设置原子操作启用位与原子操作类型的值。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_store_atomic_config_v2_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_set_store_atomic_config_v2（废弃）

该接口已废弃。原子加操作请使用asc_atomic_add实现。 设置原子操作启用位与原子操作类型的值。
函数原型：void asc_set_store_atomic_config_v2(uint16_t type, uint16_t op)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscGetStoreAtomicConfig](asc_get_store_atomic_config.md)（`related`）：V2 已废弃，迁移需用当前 setter 并以 getter 验证。
- [asc_atomic_add](../../../simt_api/atomic_operations/asc_atomic_add.md)（`related`）：废弃卡明确要求原子加迁移到 asc_atomic_add；目标接口给出原子读改写、返回旧值、内存空间和浮点顺序敏感约束。
- [AscStoreAtomicConfig](../struct/asc_store_atomic_config.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《asc_set_store_atomic_config_v2（废弃）》具体提供“该接口已废弃。原子加操作请使用asc_atomic_add实现。 设置原子操作启用位与原子操作类型的值。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
<!-- cannbot:related:end -->
