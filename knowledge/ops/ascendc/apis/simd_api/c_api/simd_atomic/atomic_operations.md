---
type: API
title: 原子操作
description: SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/atomic_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 原子操作

- **asc_get_store_atomic_config**

- **asc_set_atomic_add**

- **asc_set_atomic_max**

- **asc_set_atomic_min**

- **asc_set_atomic_none**

- **asc_set_store_atomic_config_v1**

- **asc_set_atomic_max_int（废弃）**

- **asc_set_atomic_min_int（废弃）**

- **asc_set_store_atomic_config_v2（废弃）**

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《原子操作》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AscStoreAtomicConfig](../struct/asc_store_atomic_config.md)（`related`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《原子操作》具体提供“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [原子操作概述](../../basic_api/atomic_operations/atomic_operations_overview.md)（`related`）：《原子操作概述》明确“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。”；它与《原子操作》的“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [原子操作概述（SIMD原子操作）](atomic_operations_overview.md)（`same_topic`）：《原子操作概述（SIMD原子操作）》明确“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。”；它与《原子操作》的“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
