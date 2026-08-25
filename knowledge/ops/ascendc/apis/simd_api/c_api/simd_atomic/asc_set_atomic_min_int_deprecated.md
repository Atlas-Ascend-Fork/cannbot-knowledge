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

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《asc_set_atomic_min_int（废弃）》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：原子取小状态会影响后续搬运，完成目标区间后需 AscSetAtomicNone 清理，避免污染无关写回。
<!-- cannbot:related:end -->
