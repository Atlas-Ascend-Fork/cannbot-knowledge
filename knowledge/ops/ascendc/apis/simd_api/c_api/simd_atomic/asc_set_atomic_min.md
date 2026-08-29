---
type: API
title: AscSetAtomicMin
description: 对后续从UB/L0C/L1到GM的数据传输开启原子比较取小，将待拷贝内容与GM已有内容比较后取最小值写入GM。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_atomic_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetAtomicMin

设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到GM的数据传输开启原子比较取小操作。数据类型支持int8_t、int16_t、half、bfloat16_t、int32_t、float。 开启原子比较取小后，后续执行搬运操作从Unified Buffer/L0C Buffer/L1 Buffer到GM时，将待拷贝的内容和GM已有内容进行比较，将最小值写入GM。 特别地，针对Ascend 950PR/Ascend 950DT，不支持L1 Buffer到GM的通路。
函数原型：void asc_set_atomic_min_int8()
约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。；该指令执行前不会对GM的数据做清零操作，开发者可以在需要时手动添加清零操作。；针对Ascend 950PR/Ascend 950DT，不支持L1 Buffer到GM的通路。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。；一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。。asc_set_atomic_min 开启的原子最小状态需要由 asc_set_atomic_none 清除，但 none 也服务 add 和 max，故两者是启用与清理的任务链而非单一 min 接口的同义面。
- [asc_set_atomic_min_int（废弃）](asc_set_atomic_min_int_deprecated.md)（`same_topic`）：该接口已废弃，请使用asc_set_atomic_min_int32替代。 设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到GM的数据传输开启原子比较取小操作。 废弃页给出迁移方向，当前接口族保留后续搬运比较取小的数据合同，支撑旧调用迁移。
<!-- cannbot:related:end -->
