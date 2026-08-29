---
type: API
title: AscStoreAlign
description: 已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post
  Update目的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_v4_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStoreAlign

该接口已废弃。其中asc_storealign_pack_postupdate_v2请使用asc_storealign_pack_quarter_postupdate实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续对齐搬出到UB的场景，并支持多种搬出模式，接口通过int32_t传入偏移，同时设置成硬件自动Post Update，用户不用更新偏移或者更新目的操作数的地址。
函数原型：void asc_storealign_postupdate(__ubuf__ int8_t*& dst_align32b, vector_int8_t src, int32_t offset, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlignPackQuarterPostupdate](asc_storealign_pack_quarter_postupdate.md)（`related`）：焦点卡给出明确迁移指令“asc_storealign_pack_postupdate_v2请使用asc_storealign_pack_quarter_postupdate实现此功能。”，候选卡定义替代接口“根据mask将src中有效元素的低8bits数据连续存储于dst_align32b中”；两卡是废弃入口到现行 b32 低 8bits 压缩搬出的直接替换关系。
<!-- cannbot:related:end -->
