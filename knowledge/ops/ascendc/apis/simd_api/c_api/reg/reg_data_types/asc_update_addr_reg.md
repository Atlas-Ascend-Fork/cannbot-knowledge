---
type: API
title: AscUpdateAddrReg
description: 更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_update_addr_reg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscUpdateAddrReg

更新地址寄存器（addr_reg），用于迭代寻址。支持1~4维偏移量设置，位宽支持b8、b16、b32三种模式：

- b8模式：每次迭代地址偏移量以1字节为单位，适用于int8_t、uint8_t等类型的操作。
- b16模式：每次迭代地址偏移量以2字节为单位，适用于half、int16_t等类型的操作。
- b32模式：每次迭代地址偏移量以4字节为单位，适用于float、int32_t等类型的操作。

每次迭代时的地址偏移量计算公式为：offset = index0×stride0 + index1×stride1 + index2×stride2 + index3×stride3，其中index_i为各维度的循环迭代变量，stride_i为各维度的步长。例如在4维场景（N, C, H, W）中，offset0对应W维（最内层），offset1对应H×W，offset2对应C×H×W，offset3对应N×C×H×W。addr_reg更新后配合asc_loadalign/asc_storealign等接口使用，在循环中按设定的偏移量自动递增UB地址。

>旧接口 asc_create_iter_reg_ 已废弃，请使用 asc_update_addr_reg_ 替代。旧接口返回类型 iter_reg 也已更名为 addr_reg。
约束：请勿在循环内使用if/else。；addr_reg必须在最内层循环体内赋值使用。；不同步长的操作数，建议使用多个addr_reg，避免地址被覆盖。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignDeintlvPostupdate](../reg_load/asc_loadalign_deintlv_postupdate.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscUpdateAddrReg》具体提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscLoadalignPostupdate](../reg_load/asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscUpdateAddrReg》明确提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalignUnpack4Postupdate](../reg_load/asc_loadalign_unpack4_postupdate.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscUpdateAddrReg》提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignUpsamplePostupdate](../reg_load/asc_loadalign_upsample_postupdate.md)（`related`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscUpdateAddrReg》明确“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [AscStoreAlignPostupdate](../reg_store/asc_storealign_postupdate.md)（`related`）：AscStoreAlignPostupdate 与《AscUpdateAddrReg》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStoreUnalignPostupdate](../reg_store/asc_storeunalign_postupdate.md)（`related`）：PostUpdate store 消费更新后的 AddrReg，展示实际下游。
- [AscStorealign1stPostupdate](../reg_store/asc_storealign_1st_postupdate.md)（`related`）：AscStorealign1stPostupdate 与《AscUpdateAddrReg》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [AscStorealignPackPostupdate](../reg_store/asc_storealign_pack_postupdate.md)（`related`）：AscStorealignPackPostupdate 与《AscUpdateAddrReg》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscUpdateMask](asc_update_mask.md)（`related`）：地址推进和有效 lane mask 往往需在同一循环同步更新。
- [asc_create_iter_reg (废弃)](asc_create_iter_reg_deprecated.md)（`related`）：废弃 IterReg 的地址推进可迁移为 AddrReg + UpdateAddrReg。
- [AddrReg](../../../basic_api/reg_vector_compute/register_data_types/addr_reg.md)（`same_topic`）：AddrReg 类型是 UpdateAddrReg 更新的核心对象。
<!-- cannbot:related:end -->
