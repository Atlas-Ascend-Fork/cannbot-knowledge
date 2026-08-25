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

- [AscLoadalign](asc_loadalign.md)（`related`）：AscLoadalignV3Deprecated 与《AscLoadalign》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
- [AscLoadalignBrcDatablock](asc_loadalign_brc_datablock.md)（`same_topic`）：AscLoadalignV3Deprecated 与《AscLoadalignBrcDatablock》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
- [AscLoadalignBrcElem2datablock](asc_loadalign_brc_elem2datablock.md)（`same_topic`）：AscLoadalignV3Deprecated 与《AscLoadalignBrcElem2datablock》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
- [AscLoadalignUnpack4](asc_loadalign_unpack4.md)（`same_topic`）：AscLoadalignV3Deprecated 与《AscLoadalignUnpack4》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
<!-- cannbot:related:end -->
