---
type: API
title: AscStoreAtomicConfig
description: 原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_store_atomic_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscStoreAtomicConfig

asc_store_atomic_config参数包含原子操作启用位与原子操作类型，用于asc_get_store_atomic_config接口使用。

字段：atomic_type：原子操作启用位，默认值：0。 0：无原子操作。 1：开启原子操作，进行原子操作的数据类型为float。 2：开启原子操作，进行原子操作的数据类型为half。 3：开启原子操作，进行原子操作的数据类型为int16_t。 4：开启原子操作，进行原子操作的数据类型为int32_t。 5：开启原子操作，进行原子操作的数据类型为int8_t。 6：开启原子操作，进行原子操作的数据类型为bfloat16_t。 其余值无具体含义。；atomic_op：原子操作类型，默认值：0。 0：求和操作。 其余值无具体含义。

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlign](../reg/reg_store/asc_storealign_v1_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。；《AscStoreAtomicConfig》说明原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。。二者在废弃StoreAlign与现行StoreAlign、PostUpdate和原子配置的差异决定UB连续搬出地址及写语义上存在可执行的直接衔接。
- [AscStoreAlign](../reg/reg_store/asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《AscStoreAtomicConfig》说明原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [AscStoreAlignPackQuarter](../reg/reg_store/asc_storealign_pack_quarter.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStoreAtomicConfig》说明原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [SetStoreAtomicConfig](../../basic_api/atomic_operations/set_store_atomic_config_isasi.md)（`related`）：SetStoreAtomicConfig 与《AscStoreAtomicConfig》的实质衔接是：SetStoreAtomicConfig 与 Get 配对，C API setter/getter 和配置结构体操作同一 Store 原子状态。
- [原子操作](../simd_atomic/atomic_operations.md)（`related`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《原子操作》具体提供“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [AscGetStoreAtomicConfig](../simd_atomic/asc_get_store_atomic_config.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《AscGetStoreAtomicConfig》具体提供“获取原子操作启用位与原子操作类型的值，可用于校验设置的原子配置是否符合预期。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [AscSetStoreAtomicConfigV1](../simd_atomic/asc_set_store_atomic_config_v1.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《AscSetStoreAtomicConfigV1》具体提供“设置原子操作启用位与原子操作类型的值。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [GetStoreAtomicConfig](../../basic_api/atomic_operations/get_store_atomic_config_isasi.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《GetStoreAtomicConfig》具体提供“获取当前原子操作的开启状态和数据类型配置。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
- [asc_set_store_atomic_config_v2（废弃）](../simd_atomic/asc_set_store_atomic_config_v2_deprecated.md)（`same_topic`）：《AscStoreAtomicConfig》的任务是“原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。”。《asc_set_store_atomic_config_v2（废弃）》具体提供“该接口已废弃。原子加操作请使用asc_atomic_add实现。 设置原子操作启用位与原子操作类型的值。”，它直接用于AscStoreAtomicConfig 的 get/set 生命周期与原子配置语义。
<!-- cannbot:related:end -->
