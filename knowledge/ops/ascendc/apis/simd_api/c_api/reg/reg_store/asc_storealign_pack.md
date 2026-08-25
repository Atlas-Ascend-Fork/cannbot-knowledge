---
type: API
title: AscStorealignPack
description: 从矢量数据寄存器压缩搬出到UB，根据mask将src中有效元素的低半部分bit数据连续存储于dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_pack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealignPack

从矢量数据寄存器压缩搬出到UB的接口，根据mask将src中有效元素的低半部分bit数据连续存储于dst_align32b中，支持数据类型为b16、b32、b64。
函数原型：void asc_storealign_pack(__ubuf__ int16_t* dst_align32b, vector_int16_t src, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscPackToHigh](../data_compress/asc_pack_to_high.md)（`related`）：AscPackToHigh 与《AscStorealignPack》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`related`）：PackQuarter 只保留 b32 元素低 8bit，而 Pack 保留低半位宽；目标压缩倍率决定接口选择。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStorealignPack》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
<!-- cannbot:related:end -->
