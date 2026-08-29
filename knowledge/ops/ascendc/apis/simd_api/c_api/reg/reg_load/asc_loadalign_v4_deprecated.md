---
type: API
title: AscLoadalignV4Deprecated
description: 已废弃的对齐搬入接口（int32_t偏移并启用Post Update），支持NORM、BRC、UP2X等多种搬入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v4_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignV4Deprecated

该接口已废弃。其中asc_loadalign_brc_postupdate_v2请使用asc_loadalign_brc_datablock_postupdate，asc_loadalign_brc_postupdate_v3请使用asc_loadalign_brc_elem2datablock_postupdate，asc_loadalign_unpack_postupdate_v2请使用asc_loadalign_unpack4_postupdate实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过int32_t传入偏移，同时设置成硬件自动Post Update，用户不用更新偏移或者更新源操作数的地址。
函数原型：void asc_loadalign_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcDatablockPostupdate](asc_loadalign_brc_datablock_postupdate.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_postupdate_v2请使用asc_loadalign_brc_datablock_postupdate，asc_loadalign_brc_postupdate_v3请使用asc_loadalign_brc_elem2datablock_postupdate，asc_loadalign_unpack_postupdate_v2请使用asc_loadalign_unpack4_postupdate实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式并启用Post Update：读取一个DataBlock（32B）并广播到VL，接口调用后自动更新源操作数地址。。废弃页把旧 brc_postupdate_v2 明确映射到新的 DataBlock Post Update 接口。
- [AscLoadalignBrcElem2datablockPostupdate](asc_loadalign_brc_elem2datablock_postupdate.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_postupdate_v2请使用asc_loadalign_brc_datablock_postupdate，asc_loadalign_brc_postupdate_v3请使用asc_loadalign_brc_elem2datablock_postupdate，asc_loadalign_unpack_postupdate_v2请使用asc_loadalign_unpack4_postupdate实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现元素到DataBlock广播搬入模式并启用Post Update：加载（VL/DataBlock）个元素的数据并将每个元素（16bit/32bit）广播到一个DataBlock（32B）中，接口调用后自动更新源操作数地址。。废弃页把旧 brc_postupdate_v3 映射到逐元素广播并自动更新地址的新接口。
- [AscLoadalignUnpack4Postupdate](asc_loadalign_unpack4_postupdate.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_postupdate_v2请使用asc_loadalign_brc_datablock_postupdate，asc_loadalign_brc_postupdate_v3请使用asc_loadalign_brc_elem2datablock_postupdate，asc_loadalign_unpack_postupdate_v2请使用asc_loadalign_unpack4_postupdate实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现UNPACK4搬入模式并启用Post Update：按无符号整型u8加载VL/4长度数据并unpack到VL长度u32类型（中间位置补0），接口调用后自动更新源操作数地址。。废弃页把旧 unpack_postupdate_v2 明确映射到新 UNPACK4 Post Update 接口。
<!-- cannbot:related:end -->
