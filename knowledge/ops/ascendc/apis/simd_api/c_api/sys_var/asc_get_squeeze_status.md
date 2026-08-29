---
type: API
title: AscGetSqueezeStatus
description: 读取squeeze操作后保存的有效数据长度值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_squeeze_status.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetSqueezeStatus

读取squeeze操作后保存至AR特殊寄存器的有效数据长度值，用于配合asc_squeeze_and_storeunalign接口获取已连续搬出的有效数据量。
函数原型：int64_t asc_get_squeeze_status()
返回值：返回int64_t类型的squeeze有效数据长度值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [asc_get_ar_spr (废弃)](asc_get_ar_spr_deprecated.md)（`related`）：该接口已废弃，请使用asc_get_squeeze_status实现此功能。 读取指定特殊寄存器的值。；读取squeeze操作后保存至AR特殊寄存器的有效数据长度值，用于配合asc_squeeze_and_storeunalign接口获取已连续搬出的有效数据量。；废弃接口明确把 AscGetSqueezeStatus 指定为替代实现；新接口给出其读取 squeeze 有效数据长度的现行合同。
<!-- cannbot:related:end -->
