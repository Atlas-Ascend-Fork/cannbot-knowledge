---
type: API
title: AscLoadalignV2Deprecated
description: 已废弃的对齐搬入接口（addr_reg偏移入参），支持NORM、BRC、UP2X等多种搬入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v2_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignV2Deprecated

该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新源操作数的地址。
函数原型：void asc_loadalign(vector_fp4x2_e1m2_t& dst, __ubuf__ fp4x2_e1m2_t* src, addr_reg offset)
约束：该接口中的src需要32B对齐。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignBrcDatablock](asc_loadalign_brc_datablock.md)（`related`）：“该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新源操作数的地址。”列出该废弃族的三条明确替换映射；“对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。”验证当前目标承载的具体广播或解压语义。两端共同支持按旧模式迁移，而不是只凭同名选择新 API。
- [AscLoadalignBrcElem2datablock](asc_loadalign_brc_elem2datablock.md)（`related`）：“该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新源操作数的地址。”列出该废弃族的三条明确替换映射；“对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现元素到DataBlock广播搬入模式：加载（VL/DataBlock）个元素的数据，并将每个元素（16bit/32bit）广播到一个DataBlock（32B）中。”验证当前目标承载的具体广播或解压语义。两端共同支持按旧模式迁移，而不是只凭同名选择新 API。
- [AscLoadalignUnpack4](asc_loadalign_unpack4.md)（`related`）：“该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新源操作数的地址。”列出该废弃族的三条明确替换映射；“对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现UNPACK4搬入模式：解压缩模式，按无符号整型u8加载VL/4长度数据，unpack到VL长度u32类型，中间位置补0。”验证当前目标承载的具体广播或解压语义。两端共同支持按旧模式迁移，而不是只凭同名选择新 API。
<!-- cannbot:related:end -->
