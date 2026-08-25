---
type: API
title: AscStoreAlignPostupdate
description: 将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到UB，启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续调用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreAlignPostupdate

将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到Unified Buffer（UB），启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续多次调用时无需手动维护目的地址。当源操作数为矢量数据寄存器时，单次搬出量为VL（256字节），支持配置掩码用于指示参与搬出的元素，掩码为1的元素写入目的地址，掩码为0的元素保留目的地址原数据。当源操作数为掩码寄存器时，单次搬出量为掩码寄存器长度（32字节），不支持配置掩码。搬运过程中数据格式与内容保持不变。本接口在Vector Function（__simd_vf__标记的函数）内使用，目的操作数为UB地址。 矢量数据寄存器搬出场景提供以下两种模式： 掩码寄存器搬出场景提供以下一种模式：
约束：非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；dst_align32b/dst起始地址需32字节对齐，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignPostupdate](../reg_load/asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscStoreAlignPostupdate》明确提供“将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到UB，启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续调用。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscStore](asc_store.md)（`related`）：AscStoreAlignPostupdate 与《AscStore》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：AscStoreAlignPostupdate 与《AscUpdateAddrReg》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [reg数据搬出](reg_store.md)（`related`）：AscStoreAlignPostupdate 与《reg数据搬出》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStoreAlign](asc_storealign_v1_deprecated.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStoreAlign》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStoreAlign](asc_storealign_v3_deprecated.md)（`same_topic`）：AscStoreAlign 与《AscStoreAlignPostupdate》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [AscStoreAlign](asc_storealign_v4_deprecated.md)（`same_topic`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《AscStoreAlignPostupdate》说明将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到UB，启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续调用。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [AscStoreAlignPackQuarterPostupdate](asc_storealign_pack_quarter_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStoreAlignPackQuarterPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStorealign 与《AscStoreAlignPostupdate》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStorealign1stPostupdate](asc_storealign_1st_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStorealign1stPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStorealignPackPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [StoreAlignNoncontinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《AscStoreAlignPostupdate》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [asc_storealign (废弃)](asc_storealign_v5_deprecated.md)（`same_topic`）：废弃说明明确要求用 asc_storealign_postupdate 替代 v5 的 repeat-stride 搬出功能。
<!-- cannbot:related:end -->
