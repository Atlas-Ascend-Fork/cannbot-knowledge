---
type: API
title: AscLoadalignBrcElem
description: 从UB对齐搬入一个元素并广播到矢量寄存器的所有元素位置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_elem.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcElem

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现BRC搬入模式：搬运一个b8/b16/b32类型的数据，并Broadcast到所有元素位置。 支持三种偏移方式：
函数原型：void asc_loadalign_brc_elem(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
