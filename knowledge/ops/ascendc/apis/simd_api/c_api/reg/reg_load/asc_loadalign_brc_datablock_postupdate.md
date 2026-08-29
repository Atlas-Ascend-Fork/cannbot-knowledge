---
type: API
title: AscLoadalignBrcDatablockPostupdate
description: 从UB对齐搬入一个DataBlock（32B）并广播到VL，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_datablock_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcDatablockPostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式并启用Post Update：读取一个DataBlock（32B）并广播到VL，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_brc_datablock_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignV4Deprecated](asc_loadalign_v4_deprecated.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_postupdate_v2请使用asc_loadalign_brc_datablock_postupdate，asc_loadalign_brc_postupdate_v3请使用asc_loadalign_brc_elem2datablock_postupdate，asc_loadalign_unpack_postupdate_v2请使用asc_loadalign_unpack4_postupdate实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式并启用Post Update：读取一个DataBlock（32B）并广播到VL，接口调用后自动更新源操作数地址。。废弃页把旧 brc_postupdate_v2 明确映射到新的 DataBlock Post Update 接口。
<!-- cannbot:related:end -->
