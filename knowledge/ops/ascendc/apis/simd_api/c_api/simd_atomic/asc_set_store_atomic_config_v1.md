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
