---
type: API
title: AscStorealignPackPostupdate
description: 从矢量或掩码寄存器压缩搬出到UB，根据mask将有效元素低半部分bit数据连续存储于dst，调用后自动更新目的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_pack_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealignPackPostupdate

从矢量数据寄存器或掩码寄存器压缩搬出到UB的接口，根据mask将src中有效元素的低半部分bit数据连续存储于dst中，接口调用后自动更新目的操作数地址。支持数据类型为b16、b32、b64。
函数原型：void asc_storealign_pack_postupdate(__ubuf__ int16_t*& dst_align32b, vector_int16_t src, int32_t offset, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscPackToHigh](../data_compress/asc_pack_to_high.md)（`related`）：AscStorealignPackPostupdate 与《AscPackToHigh》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscPackToLow](../data_compress/asc_pack_to_low.md)（`related`）：AscStorealignPackPostupdate 与《AscPackToLow》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscUnpack](../data_compress/asc_unpack.md)（`related`）：AscStorealignPackPostupdate 与《AscUnpack》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：AscStorealignPackPostupdate 与《AscUpdateAddrReg》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [reg数据搬出](reg_store.md)（`related`）：AscStorealignPackPostupdate 与《reg数据搬出》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscStore](asc_store.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStore》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`same_topic`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《AscStorealignPackPostupdate》说明从矢量或掩码寄存器压缩搬出到UB，根据mask将有效元素低半部分bit数据连续存储于dst，调用后自动更新目的地址。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlignPackQuarterPostupdate](asc_storealign_pack_quarter_postupdate.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStorealignPackPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStorealignPack](asc_storealign_pack.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStorealignPack》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
<!-- cannbot:related:end -->
