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

- [AscSetStoreAtomicConfigV1](asc_set_store_atomic_config_v1.md)（`same_topic`）：设置原子操作启用位与原子操作类型的值；使用完成后，建议通过asc_set_atomic_none清空原子操作的状态，以免影响后续相关指令功能。两卡围绕 store atomic 配置的同一核心状态；v1 补充 A2/A3 清理状态和 GM 预清零合同，v2 记录 950 接口已废弃。
<!-- cannbot:related:end -->
