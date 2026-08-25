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

<!-- cannbot:related:start -->
## 相关

- [SetAtomicType](set_atomic_type.md)（`related`）：GetStoreAtomicConfig 可读取当前搬出原子配置，用于验证 SetAtomicType 后的模式及排查残留状态。
- [AscGetStoreAtomicConfig](../../c_api/simd_atomic/asc_get_store_atomic_config.md)（`same_topic`）：C++ API 读取同一 store atomic 配置。
- [AscStoreAtomicConfig](../../c_api/struct/asc_store_atomic_config.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《GetStoreAtomicConfig》具体提供“获取当前原子操作的开启状态和数据类型配置。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [SetStoreAtomicConfig](set_store_atomic_config_isasi.md)（`same_topic`）：SetStoreAtomicConfig 与《GetStoreAtomicConfig》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
<!-- cannbot:related:end -->
