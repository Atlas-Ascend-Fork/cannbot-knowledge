---
type: API
title: AscLoadalignUnpack4Postupdate
description: 从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_unpack4_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUnpack4Postupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现UNPACK4搬入模式并启用Post Update：按无符号整型u8加载VL/4长度数据并unpack到VL长度u32类型（中间位置补0），接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_unpack4_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignV4Deprecated](asc_loadalign_v4_deprecated.md)（`related`）：废弃页把 unpack_postupdate_v2 的替代路径指定为 AscLoadalignUnpack4Postupdate。
- [AscUnpack](../data_compress/asc_unpack.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscUnpack》提供“将源操作数低半或高半部分元素扩充位宽后写入目的操作数，支持无符号、有符号及bool类型”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscUpdateAddrReg》提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [UnPack](../../../basic_api/reg_vector_compute/data_compression/un_pack.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《UnPack》提供“将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [UnPack](../../../basic_api/reg_vector_compute/mask_reg_compute/un_pack.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《UnPack》提供“根据低位或高位模式，将src的低半部分或高半部分展开到dst，每bit展开为2bit。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignPostupdate》提供“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignUnpack4](asc_loadalign_unpack4.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignUnpack4》提供“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，中间位置补0。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignUnpackPostupdate](asc_loadalign_unpack_postupdate.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignUnpackPostupdate》提供“从UB对齐搬入数据并实现解压缩，调用后自动更新源地址。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
<!-- cannbot:related:end -->
