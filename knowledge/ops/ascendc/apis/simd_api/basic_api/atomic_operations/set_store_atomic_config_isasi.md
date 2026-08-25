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

- [AscGetStoreAtomicConfig](../../c_api/simd_atomic/asc_get_store_atomic_config.md)（`related`）：SetStoreAtomicConfig 与《AscGetStoreAtomicConfig》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
- [AscSetStoreAtomicConfigV1](../../c_api/simd_atomic/asc_set_store_atomic_config_v1.md)（`related`）：SetStoreAtomicConfig 与《AscSetStoreAtomicConfigV1》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
- [AscStoreAtomicConfig](../../c_api/struct/asc_store_atomic_config.md)（`related`）：SetStoreAtomicConfig 与《AscStoreAtomicConfig》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
- [GetStoreAtomicConfig](get_store_atomic_config_isasi.md)（`same_topic`）：SetStoreAtomicConfig 与《GetStoreAtomicConfig》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
<!-- cannbot:related:end -->
