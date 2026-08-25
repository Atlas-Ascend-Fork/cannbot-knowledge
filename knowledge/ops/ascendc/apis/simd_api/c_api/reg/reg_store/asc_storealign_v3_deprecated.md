---
type: API
title: AscStoreAlign
description: 已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，通过int32_t传入偏移。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_v3_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStoreAlign

该接口已废弃。其中asc_storealign_pack_v2请使用asc_storealign_pack_quarter实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续对齐搬出到UB的场景，并支持多种搬出模式，接口通过int32_t传入偏移，用户可以选择更新偏移或者更新目的操作数的地址。
函数原型：void asc_storealign(__ubuf__ int8_t* dst_align32b, vector_int8_t src, int32_t offset, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlign](asc_storealign_v1_deprecated.md)（`same_topic`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。；《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，通过int32_t传入偏移。。二者在废弃StoreAlign与现行StoreAlign、PostUpdate和原子配置的差异决定UB连续搬出地址及写语义上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v2_deprecated.md)（`same_topic`）：AscStoreAlign 与《AscStoreAlign》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [AscStoreAlign](asc_storealign_v4_deprecated.md)（`same_topic`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，通过int32_t传入偏移。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`same_topic`）：废弃 AscStoreAlign 页明确把 asc_storealign_pack_v2 替换为 AscStoreAlignPackQuarter；两卡围绕同一 b32→低 8 bit 压缩对齐搬出合同，后者是推荐入口。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：AscStoreAlign 与《AscStoreAlignPostupdate》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStoreAlign 与《AscStorealign》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [StoreAlignContinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md)（`same_topic`）：AscStoreAlign 与《StoreAlignContinuous》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`same_topic`）：AscStoreAlign 与《废弃接口》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
<!-- cannbot:related:end -->
