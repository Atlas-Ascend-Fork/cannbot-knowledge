---
type: API
title: AscStoreAlignPackQuarterPostupdate
description: 从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型，调用后自动更新目的操作数地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_pack_quarter_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreAlignPackQuarterPostupdate

从矢量数据寄存器压缩搬出到UB的接口，根据mask将src中有效元素的低8bits数据连续存储于dst_align32b中，支持数据类型为b32，接口调用后自动更新目的操作数地址。
函数原型：void asc_storealign_pack_quarter_postupdate(__ubuf__ int32_t*& dst_align32b, vector_int32_t src, int32_t offset, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlign](asc_storealign_v4_deprecated.md)（`related`）：焦点卡给出明确迁移指令“asc_storealign_pack_postupdate_v2请使用asc_storealign_pack_quarter_postupdate实现此功能。”，候选卡定义替代接口“根据mask将src中有效元素的低8bits数据连续存储于dst_align32b中”；两卡是废弃入口到现行 b32 低 8bits 压缩搬出的直接替换关系。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`related`）：焦点卡写明“支持Post Update模式，接口调用后自动更新目的操作数地址”，候选卡写明“int32_t*& dst_align32b”。基础卡说明可自更新，专用变体以引用指针和 offset 明确 ABI，避免误用普通指针原型。
<!-- cannbot:related:end -->
