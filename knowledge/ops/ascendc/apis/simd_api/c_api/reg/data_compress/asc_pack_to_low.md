---
type: API
title: AscPackToLow
description: 将源操作数元素按位压缩写入目的操作数低半部分，支持bool、b16、b32、b64等位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_pack_to_low.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscPackToLow

将源操作数中的元素选取偶数位bit(bool)、低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分。
当源操作数为vector_bool时，其按bit位进行压缩，每2bit将其中的低位bit存储至目的操作数的低半部分。

参数：dst(输出): 目的操作数（矢量数据寄存器/掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器/掩码寄存器）。

支持数据类型：uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlignPackQuarter](../reg_store/asc_storealign_pack_quarter.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscPackToLow》说明将源操作数元素按位压缩写入目的操作数低半部分，支持bool、b16、b32、b64等位宽模式。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStorealignPackPostupdate](../reg_store/asc_storealign_pack_postupdate.md)（`related`）：AscStorealignPackPostupdate 与《AscPackToLow》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscUnpack](asc_unpack.md)（`related`）：PackToLow 将低位压入半宽布局，AscUnpack 可从 LOWER/HIGHER 半区按零扩展或符号扩展恢复宽寄存器表示，构成压缩布局的后续展开链。
- [AscPackToHigh](asc_pack_to_high.md)（`same_topic`）：AscPackToHigh 与《AscPackToLow》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscUnsqueeze](asc_unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《AscPackToLow》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [asc_pack (废弃)](asc_pack_deprecated.md)（`same_topic`）：废弃 asc_pack 的低半区行为由 AscPackToLow 显式替代，消除旧接口的隐式目标选择。
<!-- cannbot:related:end -->
