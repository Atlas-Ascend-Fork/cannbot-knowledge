---
type: API
title: AscGetCtrl
description: 读取CTRL寄存器特定比特位上的值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_ctrl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetCtrl

读取CTRL寄存器（控制寄存器）特定比特位上的值。
函数原型：int64_t asc_get_ctrl()
返回值：CTRL寄存器的值。具体含义请参考asc_set_ctrl中的描述。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
