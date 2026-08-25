---
type: API
title: AscLoadalignPostupdate
description: 从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignPostupdate

将Unified Buffer（UB）中起始地址32字节对齐的数据搬入矢量数据寄存器或掩码寄存器，搬运过程中数据格式和内容保持不变。搬运完成后启用Post Update模式，自动更新源地址指针。本接口提供两种功能模式： 本接口仅在AIV上生效，非AIV调用直接返回。
约束：本接口仅在AIV上生效，非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；实际读取的UB地址和偏移后的UB地址必须32字节对齐，并且在UB地址空间内且不越界，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoad](asc_load.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoad》明确提供“从UB非32字节对齐的源地址搬运VL大小的数据到矢量数据寄存器。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalign](asc_loadalign.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadalign》明确提供“从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalignV4Deprecated](asc_loadalign_v4_deprecated.md)（`related`）：对普通 postupdate 模式，废弃的 V4 统一入口应迁移到 AscLoadalignPostupdate。
- [AscLoadunalign](asc_loadunalign.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadunalign》明确提供“从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadunalignPre](asc_loadunalign_pre.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadunalignPre》明确提供“用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscStoreAlignPostupdate](../reg_store/asc_storealign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscStoreAlignPostupdate》明确提供“将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到UB，启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续调用。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscUpdateAddrReg》明确提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [LoadAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_align_mask_reg.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《LoadAlign》明确提供“将数据从UB搬运至MaskReg，支持普通搬运、PostUpdate扩展搬运和AddrReg偏移量三种接口，可通过MaskDist配置上采样、下采样等数据分布模式。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [reg数据搬入](reg_load.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《reg数据搬入》明确提供“寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalignDeintlvPostupdate](asc_loadalign_deintlv_postupdate.md)（`same_topic`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadalignDeintlvPostupdate》明确提供“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalignUnpack4Postupdate](asc_loadalign_unpack4_postupdate.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignPostupdate》提供“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignUpsamplePostupdate](asc_loadalign_upsample_postupdate.md)（`same_topic`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscLoadalignPostupdate》明确“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [asc_loadalign (废弃)](asc_loadalign_v5_deprecated.md)（`same_topic`）：废弃 repeat-stride asc_loadalign 正文明确迁移到 asc_loadalign_postupdate；替代接口完成对齐搬入后自动更新源地址。
<!-- cannbot:related:end -->
