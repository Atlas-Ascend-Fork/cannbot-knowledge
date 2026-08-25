---
type: API
title: GetStoreAtomicConfig
description: 获取当前原子操作的开启状态和数据类型配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/GetStoreAtomicConfig_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetStoreAtomicConfig

获取当前Store指令的原子操作配置。

函数原型：__aicore__ inline AtomicType GetStoreAtomicConfig()。参数：无。返回值：当前原子操作类型（AtomicType枚举）。约束：与SetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。
