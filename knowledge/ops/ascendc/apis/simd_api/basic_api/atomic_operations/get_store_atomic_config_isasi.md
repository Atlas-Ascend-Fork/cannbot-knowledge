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

- [SetStoreAtomicConfig](set_store_atomic_config_isasi.md)（`related`）：函数原型：__aicore__ inline void SetStoreAtomicConfig(AtomicType atomicType)。参数：atomicType为原子操作类型枚举。约束：与GetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。；函数原型：__aicore__ inline AtomicType GetStoreAtomicConfig()。参数：无。返回值：当前原子操作类型（AtomicType枚举）。约束：与SetStoreAtomicConfig配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。；前者写入 Store 原子配置，后者读取当前类型，形成显式配套的状态设置与核验链。
- [AscGetStoreAtomicConfig](../../c_api/simd_atomic/asc_get_store_atomic_config.md)（`same_topic`）：获取原子操作启用位与原子操作类型的值，可用于校验asc_set_store_atomic_config_v1和asc_set_store_atomic_config_v2（废弃）设置的原子操作启用位和原子操作类型的值是否符合预期。；获取当前Store指令的原子操作配置。。二者都读取 Store 原子配置，前者是 C API 配置结构校验接口，后者是 Basic API 返回 AtomicType 的 ISASI 接口，形成同主题的 API 表面映射。
<!-- cannbot:related:end -->
