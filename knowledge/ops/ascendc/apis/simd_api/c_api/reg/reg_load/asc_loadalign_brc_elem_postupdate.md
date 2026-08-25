---
type: API
title: AscLoadalignBrcElemPostupdate
description: 从UB对齐搬入一个元素并广播到所有元素位置，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_elem_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcElemPostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现BRC搬入模式并启用Post Update：搬运一个b8/b16/b32类型的数据并Broadcast到所有元素位置，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_brc_elem_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcElem](asc_loadalign_brc_elem.md)（`same_topic`）：The post-update variant performs the same aligned broadcast load while additionally advancing the source address for looped consumption.
<!-- cannbot:related:end -->
