---
type: API
title: AscGetBlockNum
description: 获取当前任务配置的核数，用于多核逻辑控制。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_block_num.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetBlockNum

获取当前任务配置的核数，用于代码内部的多核逻辑控制等。 此接口后续版本会废弃，请使用内置变量block_num。
函数原型：int64_t asc_get_block_num()
返回值：当前任务配置的核数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
