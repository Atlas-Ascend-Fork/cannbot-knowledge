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
