---
type: API
title: AscGetFftsBaseAddr
description: 获取核间同步寄存器的基地址。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_ffts_base_addr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetFftsBaseAddr

获取核间同步寄存器的基地址。需要在Host侧调用接口aclrtGetHardwareSyncAddr获取核间同步寄存器的基地址，并作为参数传入asc_set_ffts_base_addr后使用。
函数原型：int64_t asc_get_ffts_base_addr()
返回值：核间同步寄存器的基地址。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetFftsBaseAddr](asc_set_ffts_base_addr.md)（`related`）：获取核间同步寄存器的基地址。需要在Host侧调用接口aclrtGetHardwareSyncAddr获取核间同步寄存器的基地址，并作为参数传入asc_set_ffts_base_addr后使用。；在asc_sync_block_wait和asc_sync_block_arrive之前使用，设置核间同步寄存器的基地址。需要在Host侧调用接口aclrtGetHardwareSyncAddr获取，并作为参数传入。；GetFftsBaseAddr 读取的正是 SetFftsBaseAddr 预先写入的核间同步寄存器基地址，两者共享 Host 获取地址后的设置与读取合同。
<!-- cannbot:related:end -->
