---
type: API
title: AscPackToHigh
description: 将源操作数元素的低位写入目的操作数的高半部分，支持b16、b32、b64和bool类型压缩。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_pack_to_high.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscPackToHigh

将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的高半部分。
当源操作数为vector_bool时，其按bit位进行压缩，每2bit将其中的低位bit存储至目的操作数的高半部分。

参数：dst(输出): 目的操作数（矢量数据寄存器/掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器/掩码寄存器）。

支持数据类型：uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlignPackQuarter](../reg_store/asc_storealign_pack_quarter.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscPackToHigh》说明将源操作数元素的低位写入目的操作数的高半部分，支持b16、b32、b64和bool类型压缩。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlignPackQuarterPostupdate](../reg_store/asc_storealign_pack_quarter_postupdate.md)（`related`）：AscPackToHigh 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscStorealignPack](../reg_store/asc_storealign_pack.md)（`related`）：AscPackToHigh 与《AscStorealignPack》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscStorealignPackPostupdate](../reg_store/asc_storealign_pack_postupdate.md)（`related`）：AscStorealignPackPostupdate 与《AscPackToHigh》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscPackToLow](asc_pack_to_low.md)（`same_topic`）：AscPackToHigh 与《AscPackToLow》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscUnpack](asc_unpack.md)（`same_topic`）：AscPackToHigh 与《AscUnpack》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscUnsqueeze](asc_unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《AscPackToHigh》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [asc_pack (废弃)](asc_pack_deprecated.md)（`same_topic`）：废弃 asc_pack 的高半区行为由 AscPackToHigh 显式替代，迁移时应选择该明确接口。
<!-- cannbot:related:end -->
