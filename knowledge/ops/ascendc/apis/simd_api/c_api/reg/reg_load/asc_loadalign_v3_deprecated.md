---
type: API
title: AscLoadalignV3Deprecated
description: 已废弃的对齐搬入接口（int32_t偏移入参），支持NORM、BRC、UP2X等多种搬入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v3_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignV3Deprecated

该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过int32_t传入偏移，用户可以选择更新偏移或者更新源操作数的地址。
函数原型：void asc_loadalign(vector_int8_t& dst, __ubuf__ int8_t* src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcDatablock](asc_loadalign_brc_datablock.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。。废弃页把旧 brc_v2 明确映射到新 DataBlock 广播接口。
- [AscLoadalignBrcElem2datablock](asc_loadalign_brc_elem2datablock.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现元素到DataBlock广播搬入模式：加载（VL/DataBlock）个元素的数据，并将每个元素（16bit/32bit）广播到一个DataBlock（32B）中。。废弃页把旧 brc_v3 明确映射到逐元素广播到 DataBlock 的接口。
- [AscLoadalignUnpack4](asc_loadalign_unpack4.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现UNPACK4搬入模式：解压缩模式，按无符号整型u8加载VL/4长度数据，unpack到VL长度u32类型，中间位置补0。。废弃页把旧 unpack_v2 明确映射到 AscLoadalignUnpack4。
<!-- cannbot:related:end -->
