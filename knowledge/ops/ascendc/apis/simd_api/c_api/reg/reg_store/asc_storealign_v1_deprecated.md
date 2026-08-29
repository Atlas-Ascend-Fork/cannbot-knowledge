---
type: API
title: AscStoreAlign
description: 已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_v1_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStoreAlign

该接口已废弃。其中asc_storealign_pack_v2请使用asc_storealign_pack_quarter实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续对齐搬出到UB的场景，并支持多种搬出模式，接口不传入偏移，需要由用户自行更新目的操作数的地址。
函数原型：void asc_storealign(__ubuf__  int8_t* dst_align32b, vector_int8_t src, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlign](asc_storealign_v2_deprecated.md)（`same_topic`）：该接口已废弃。其中asc_storealign_pack_v2请使用asc_storealign_pack_quarter实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续对齐搬出到UB的场景，并支持多种搬出模式，接口不传入偏移，需要由用户自行更新目的操作数的地址。；该接口已废弃。其中asc_storealign_pack_v2请使用asc_storealign_pack_quarter实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续对齐搬出到UB的场景，并支持多种搬出模式，接口通过地址寄存器传入偏移，用户可以选择更新偏移或者更新目的操作数的地址。。两卡是同一废弃 AscStoreAlign 契约的 V1/V2 变体，核心搬出语义相同，差异是偏移由调用者地址更新还是地址寄存器传入。
<!-- cannbot:related:end -->
