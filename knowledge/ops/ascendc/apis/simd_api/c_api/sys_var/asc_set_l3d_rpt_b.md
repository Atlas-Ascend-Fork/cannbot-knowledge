---
type: API
title: AscSetL3dRptB
description: 设置asc_copy_l12l0a/l0b的2D格式搬运repeat参数。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l3d_rpt_b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL3dRptB

用于设置接口asc_copy_l12l0a、asc_copy_l12l0b的2D格式搬运的repeat参数。
函数原型：void asc_set_l3d_rpt_b(uint64_t config)
约束：需要配合接口asc_copy_l12l0a、asc_copy_l12l0b使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
