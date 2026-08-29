---
type: API
title: SetStoreAtomicConfig
description: 设置原子操作的开启位和操作类型，支持多种数据类型配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetStoreAtomicConfig_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetStoreAtomicConfig

设置Store指令的原子操作配置，用于控制Scalar单元对GM的原子写入行为。

函数原型：__aicore__ inline void SetStoreAtomicConfig(AtomicType atomicType)。参数：atomicType为原子操作类型枚举。约束：与GetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [GetStoreAtomicConfig](get_store_atomic_config_isasi.md)（`related`）：函数原型：__aicore__ inline void SetStoreAtomicConfig(AtomicType atomicType)。参数：atomicType为原子操作类型枚举。约束：与GetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。；函数原型：__aicore__ inline AtomicType GetStoreAtomicConfig()。参数：无。返回值：当前原子操作类型（AtomicType枚举）。约束：与SetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。；前者写入 Store 原子配置，后者读取当前类型，形成显式配套的状态设置与核验链。
<!-- cannbot:related:end -->
