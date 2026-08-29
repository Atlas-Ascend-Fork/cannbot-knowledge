---
type: API
title: AscLoadalignBrcDatablock
description: 从UB对齐搬入一个DataBlock（32B）并广播到VL。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_brc_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignBrcDatablock

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。 支持三种偏移方式：
函数原型：void asc_loadalign_brc_datablock(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignV1Deprecated](asc_loadalign_v1_deprecated.md)（`related`）：“该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口不传入偏移，需要由用户自行更新源操作数的地址。”逐名指定废弃入口的迁移目标；“对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。”给出该目标保留的具体搬入语义。组合阅读可按旧枚举选择唯一替代接口，而非泛化到同目录任意 LoadAlign。
- [AscLoadalignV2Deprecated](asc_loadalign_v2_deprecated.md)（`related`）：“该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新源操作数的地址。”列出该废弃族的三条明确替换映射；“对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。”验证当前目标承载的具体广播或解压语义。两端共同支持按旧模式迁移，而不是只凭同名选择新 API。
- [AscLoadalignV3Deprecated](asc_loadalign_v3_deprecated.md)（`same_topic`）：该接口已废弃。其中asc_loadalign_brc_v2请使用asc_loadalign_brc_datablock，asc_loadalign_brc_v3请使用asc_loadalign_brc_elem2datablock，asc_loadalign_unpack_v2请使用asc_loadalign_unpack4实现此功能。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现DataBlock广播搬入模式：读取一个DataBlock（32B），并广播到VL。。废弃页把旧 brc_v2 明确映射到新 DataBlock 广播接口。
<!-- cannbot:related:end -->
