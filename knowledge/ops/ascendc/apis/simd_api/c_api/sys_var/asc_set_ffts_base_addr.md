---
type: API
title: AscSetFftsBaseAddr
description: 设置核间同步寄存器的基地址。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_ffts_base_addr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetFftsBaseAddr

在asc_sync_block_wait和asc_sync_block_arrive之前使用，设置核间同步寄存器的基地址。需要在Host侧调用接口aclrtGetHardwareSyncAddr获取，并作为参数传入。
函数原型：void asc_set_ffts_base_addr(uint64_t config)
约束：在使用asc_sync_block_wait和asc_sync_block_arrive之前必须使用本接口设置基地址。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
