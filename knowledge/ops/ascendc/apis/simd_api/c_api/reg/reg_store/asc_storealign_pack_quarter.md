---
type: API
title: AscStoreAlignPackQuarter
description: 从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post
  Update模式，调用后自动更新目的操作数地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_pack_quarter.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreAlignPackQuarter

从矢量数据寄存器压缩搬出到UB的接口，根据mask将src中有效元素的低8bits数据连续存储于dst_align32b中，支持数据类型为b32。 支持Post Update模式，接口调用后自动更新目的操作数地址。
函数原型：void asc_storealign_pack_quarter(__ubuf__ int32_t* dst_align32b, vector_int32_t src, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscPackToHigh](../data_compress/asc_pack_to_high.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscPackToHigh》说明将源操作数元素的低位写入目的操作数的高半部分，支持b16、b32、b64和bool类型压缩。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscPackToLow](../data_compress/asc_pack_to_low.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscPackToLow》说明将源操作数元素按位压缩写入目的操作数低半部分，支持bool、b16、b32、b64等位宽模式。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v2_deprecated.md)（`related`）：废弃说明明确 asc_storealign_pack_v2 应迁移为 asc_storealign_pack_quarter，后者是对应的替代接口。
- [AscStoreAtomicConfig](../../struct/asc_store_atomic_config.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStoreAtomicConfig》说明原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStorealignPack](asc_storealign_pack.md)（`related`）：PackQuarter 只保留 b32 元素低 8bit，而 Pack 保留低半位宽；目标压缩倍率决定接口选择。
- [reg数据搬出](reg_store.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《reg数据搬出》说明寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v3_deprecated.md)（`same_topic`）：废弃 AscStoreAlign 页明确把 asc_storealign_pack_v2 替换为 AscStoreAlignPackQuarter；两卡围绕同一 b32→低 8 bit 压缩对齐搬出合同，后者是推荐入口。
- [AscStoreAlignPackQuarterPostupdate](asc_storealign_pack_quarter_postupdate.md)（`same_topic`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStoreAlignPackQuarterPostupdate》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型，调用后自动更新目的操作数地址。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`same_topic`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStorealignPackPostupdate》说明从矢量或掩码寄存器压缩搬出到UB，根据mask将有效元素低半部分bit数据连续存储于dst，调用后自动更新目的地址。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
<!-- cannbot:related:end -->
