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

- [AscLoadalignBrcDatablockPostupdate](asc_loadalign_brc_datablock_postupdate.md)（`related`）：废弃页明确要求 brc_postupdate_v2 迁移到 AscLoadalignBrcDatablockPostupdate。
- [AscLoadalignBrcElem2datablockPostupdate](asc_loadalign_brc_elem2datablock_postupdate.md)（`related`）：废弃页明确要求 brc_postupdate_v3 迁移到 Elem2datablock Postupdate 接口。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：对普通 postupdate 模式，废弃的 V4 统一入口应迁移到 AscLoadalignPostupdate。
- [AscLoadalignUnpack4Postupdate](asc_loadalign_unpack4_postupdate.md)（`related`）：废弃页把 unpack_postupdate_v2 的替代路径指定为 AscLoadalignUnpack4Postupdate。
<!-- cannbot:related:end -->
