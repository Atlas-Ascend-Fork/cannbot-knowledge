---
type: API
title: AscGetMaskSpr
description: 从特殊功能寄存器读取mask值，并按b16或b32数据类型格式化后返回
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_get_mask_spr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetMaskSpr

从SPR（Special Purpose Register）中读取mask值，并按数据类型格式化后返回。
函数原型：vector_bool asc_get_mask_spr_b16()
返回值：vector_bool，掩码寄存器。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
