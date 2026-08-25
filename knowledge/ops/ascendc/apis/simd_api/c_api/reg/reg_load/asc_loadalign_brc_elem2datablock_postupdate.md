---
type: API
title: AscLoadalignBrcElem2datablockPostupdate
description: 从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_elem2datablock_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcElem2datablockPostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现元素到DataBlock广播搬入模式并启用Post Update：加载（VL/DataBlock）个元素的数据并将每个元素（16bit/32bit）广播到一个DataBlock（32B）中，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_brc_elem2datablock_postupdate(vector_int16_t& dst, __ubuf__ int16_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
