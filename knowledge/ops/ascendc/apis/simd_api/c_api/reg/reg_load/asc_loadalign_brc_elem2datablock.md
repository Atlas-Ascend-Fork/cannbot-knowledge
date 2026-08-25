---
type: API
title: AscLoadalignBrcElem2datablock
description: 从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_elem2datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcElem2datablock

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现元素到DataBlock广播搬入模式：加载（VL/DataBlock）个元素的数据，并将每个元素（16bit/32bit）广播到一个DataBlock（32B）中。 支持三种偏移方式：
函数原型：void asc_loadalign_brc_elem2datablock(vector_int16_t& dst, __ubuf__ int16_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcDatablock](asc_loadalign_brc_datablock.md)（`related`）：《AscLoadalignBrcElem2datablock》明确“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中。”；它与《AscLoadalignBrcDatablock》的“从UB对齐搬入一个DataBlock（32B）并广播到VL。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscLoadalignV1Deprecated](asc_loadalign_v1_deprecated.md)（`related`）：旧 asc_loadalign_brc_v3 应迁移到元素到 DataBlock 广播接口，避免误用整块广播版本。
- [AscLoadalignV2Deprecated](asc_loadalign_v2_deprecated.md)（`related`）：废弃接口按元素到 DataBlock 广播的能力由该专用接口承接，明确 16/32bit 元素各自广播为 32B。
- [AscLoadalignBrcElem2datablockPostupdate](asc_loadalign_brc_elem2datablock_postupdate.md)（`same_topic`）：《AscLoadalignBrcElem2datablockPostupdate》明确“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中，调用后自动更新源地址。”；它与《AscLoadalignBrcElem2datablock》的“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscLoadalignV3Deprecated](asc_loadalign_v3_deprecated.md)（`same_topic`）：AscLoadalignV3Deprecated 与《AscLoadalignBrcElem2datablock》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
- [Brcb](../../../basic_api/memory_vector_compute/data_padding/brcb.md)（`same_topic`）：焦点处理Brcb 把 8 个输入分别广播到 8 个 DataBlock 的填充模式；AscLoadalignBrcElem2datablock正文说明“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中”。候选提供同一 DataBlock 广播在 C API/Reg load 中的等价形态或标量广播替代。
<!-- cannbot:related:end -->
