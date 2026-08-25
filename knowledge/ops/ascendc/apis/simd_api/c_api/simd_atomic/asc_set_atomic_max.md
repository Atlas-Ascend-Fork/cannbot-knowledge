---
type: API
title: AscSetAtomicMax
description: 对后续从UB/L0C/L1到GM的数据传输开启原子比较取大，将待拷贝内容与GM已有内容比较后取最大值写入GM。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_atomic_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetAtomicMax

设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到GM的数据传输开启原子比较取大操作。数据类型支持int8_t、int16_t、half、bfloat16_t、int32_t、float。 开启原子比较取大后，后续执行搬运操作从Unified Buffer/L0C Buffer/L1 Buffer到GM时，将待拷贝的内容和GM已有内容进行比较，将最大值写入GM。 特别地，针对Ascend 950PR/Ascend 950DT，不支持L1 Buffer到GM的通路。
函数原型：void asc_set_atomic_max_int8()
约束：使用结束后，建议通过asc_set_atomic_none关闭原子最大操作，以免影响后续相关指令功能。；该指令执行前不会对GM的数据做清零操作，开发者可以在需要时手动添加清零操作。；针对Ascend 950PR/Ascend 950DT，不支持L1 Buffer到GM的通路。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《AscSetAtomicMax》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：AscSetAtomicMax 会影响后续 UB/L0C/L1→GM 写回，完成目标原子区间后必须用 AscSetAtomicNone 恢复非原子状态。
- [SetAtomicMax](../../basic_api/atomic_operations/set_atomic_max_isasi.md)（`related`）：SetAtomicMax 与《AscSetAtomicMax》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [AscAtomicMax](../scalar_compute/asc_atomic_max.md)（`same_topic`）：AscAtomicMax 与《AscSetAtomicMax》的衔接是：AscAtomicMax 是原子最大值更新；SIMT/basic AtomicMax 提供同一竞争更新语义，SetAtomicMax/AscSetAtomicMax 则配置后续搬运执行该原子操作。
- [asc_set_atomic_max_int（废弃）](asc_set_atomic_max_int_deprecated.md)（`same_topic`）：asc_set_atomic_max_int（废弃） 的核心契约是“该接口已废弃，请使用asc_set_atomic_max_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最大值写入GM”；AscSetAtomicMax 补充“对后续从UB/L0C/L1到GM的数据传输开启原子比较取大，将待拷贝内容与GM已有内容比较后取最大值写入GM”。
<!-- cannbot:related:end -->
