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

- [AscGetStoreAtomicConfig](asc_get_store_atomic_config.md)（`related`）：设置原子操作启用位与原子操作类型的值。；获取原子操作启用位与原子操作类型的值，可用于校验asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）设置的原子操作启用位和原子操作类型的值是否符合预期。 Ascend 950PR/Ascend 950DT产品上该接口已废弃。原子加操作可以直接使用asc_atomic_add实现。无需再对原子操作启用位和原子操作类型的值进行配置和校验。；前者写配置，后者读取并核验配置，同时给出 950 上的废弃迁移边界。
- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：约束：使用完成后，建议通过asc_set_atomic_none清空原子操作的状态，以免影响后续相关指令功能。；该指令执行前不会对GM的数据做清零操作，开发者需在需要时手动添加清零操作。；清空原子操作的状态。一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。；焦点要求使用结束后清状态，目标提供关闭动作，形成原子配置生命周期。
- [asc_set_store_atomic_config_v2（废弃）](asc_set_store_atomic_config_v2_deprecated.md)（`same_topic`）：设置原子操作启用位与原子操作类型的值；使用完成后，建议通过asc_set_atomic_none清空原子操作的状态，以免影响后续相关指令功能。两卡围绕 store atomic 配置的同一核心状态；v1 补充 A2/A3 清理状态和 GM 预清零合同，v2 记录 950 接口已废弃。
<!-- cannbot:related:end -->
