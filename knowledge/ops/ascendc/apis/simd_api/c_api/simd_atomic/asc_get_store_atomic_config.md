---
type: API
title: AscGetStoreAtomicConfig
description: 获取原子操作启用位与原子操作类型的值，可用于校验设置的原子配置是否符合预期。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_get_store_atomic_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetStoreAtomicConfig

获取原子操作启用位与原子操作类型的值，可用于校验asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）设置的原子操作启用位和原子操作类型的值是否符合预期。 Ascend 950PR/Ascend 950DT产品上该接口已废弃。原子加操作可以直接使用asc_atomic_add实现。无需再对原子操作启用位和原子操作类型的值进行配置和校验。
函数原型：void asc_get_store_atomic_config(asc_store_atomic_config& config)
约束：需配合asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）接口使用，该接口用于设置原子操作启用位和原子操作类型的值。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
