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

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcDatablock](asc_loadalign_brc_datablock.md)（`related`）：《AscLoadalignBrcElem2datablockPostupdate》明确“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中，调用后自动更新源地址。”；它与《AscLoadalignBrcDatablock》的“从UB对齐搬入一个DataBlock（32B）并广播到VL。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscLoadalignV4Deprecated](asc_loadalign_v4_deprecated.md)（`related`）：废弃页明确要求 brc_postupdate_v3 迁移到 Elem2datablock Postupdate 接口。
- [AscLoadalignBrcElem2datablock](asc_loadalign_brc_elem2datablock.md)（`same_topic`）：《AscLoadalignBrcElem2datablockPostupdate》明确“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中，调用后自动更新源地址。”；它与《AscLoadalignBrcElem2datablock》的“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中。”在实际调用参数、数据流或结果校验上直接衔接。
- [Brcb](../../../basic_api/memory_vector_compute/data_padding/brcb.md)（`same_topic`）：焦点处理Brcb 把 8 个输入分别广播到 8 个 DataBlock 的填充模式；AscLoadalignBrcElem2datablockPostupdate正文说明“从UB加载多个元素并将每个元素广播到一个DataBlock（32B）中，调用后自动更新源地址”。候选提供同一 DataBlock 广播在 C API/Reg load 中的等价形态或标量广播替代。
<!-- cannbot:related:end -->
