---
type: API
title: asc_clear_ar_spr
description: 该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/system_variables_access/asc_clear_ar_spr_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_clear_ar_spr

该接口已废弃。请使用asc_squeeze_and_storeunalign_init实现此功能。 对AR特殊寄存器进行清零操作。AR寄存器用于配合asc_squeeze_with_status使用：当调用asc_squeeze_with_status时，有效元素的总字节数会被存入AR寄存器。在调用asc_squeeze_with_status之前，需调用该接口将AR寄存器清零。
函数原型：void asc_clear_ar_spr()
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
