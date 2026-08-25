---
type: API
title: asc_get_status
description: 获取当前核的状态寄存器信息，返回int64_t类型的状态值，各比特位反映浮点溢出、下溢、NaN/INF输入及CUBE累加溢出等异常情况，供开发者进行错误检测。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_status.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_get_status

获取状态信息。
函数原型：int64_t asc_get_status()
返回值：状态信息。各bit含义如下：
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
