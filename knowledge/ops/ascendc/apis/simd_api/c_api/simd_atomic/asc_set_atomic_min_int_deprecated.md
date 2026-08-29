---
type: API
title: asc_set_atomic_min_int（废弃）
description: 该接口已废弃，请使用asc_set_atomic_min_int32替代。 头文件路径："c_api/atomic/atomic.h"。
  设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最小值写入GM。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_atomic_min_int_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_set_atomic_min_int（废弃）

该接口已废弃，请使用asc_set_atomic_min_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最小值写入GM。
函数原型：[[deprecated("NOTICE: asc_set_atomic_min_int is deprecated. Please use asc_set_atomic_min_int32 instead.")]]
约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`same_topic`）：该接口已废弃，请使用asc_set_atomic_min_int32替代。 设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到GM的数据传输开启原子比较取小操作。 废弃页给出迁移方向，当前接口族保留后续搬运比较取小的数据合同，支撑旧调用迁移。
- [AscSetAtomicNone](asc_set_atomic_none.md)（`same_topic`）：约束：使用结束后，建议通过asc_set_atomic_none关闭原子最小操作，以免影响后续相关指令功能。 清空原子操作的状态。一般和asc_set_atomic_add，asc_set_atomic_max，asc_set_atomic_min接口配合使用，用于在完成原子操作后关闭原子操作，避免影响后续功能。 旧接口的约束与 None 的状态清理语义共同确定原子最小完成后的收尾调用。
<!-- cannbot:related:end -->
