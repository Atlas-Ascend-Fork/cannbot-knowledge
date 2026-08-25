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

- [AscPackToHigh](../data_compress/asc_pack_to_high.md)（`related`）：AscPackToHigh 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`same_topic`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStoreAlignPackQuarterPostupdate》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型，调用后自动更新目的操作数地址。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
<!-- cannbot:related:end -->
