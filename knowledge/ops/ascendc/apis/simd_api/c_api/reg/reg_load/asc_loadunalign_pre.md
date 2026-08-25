---
type: API
title: AscLoadunalignPre
description: 用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadunalign_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadunalignPre

用于在进行非对齐数据搬入前的初始化，需配合asc_loadunalign接口使用。
函数原型：void asc_loadunalign_pre(vector_load_unalign& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
