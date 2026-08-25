---
type: API
title: AscStorealign
description: 将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStorealign

将矢量数据寄存器或掩码寄存器中的数据以对齐的方式搬出到Unified Buffer（UB）。当源操作数为矢量数据寄存器时，单次搬出量为VL（256字节），支持配置掩码用于指示参与搬出的元素，掩码为1的元素写入目的地址，掩码为0的元素保留目的地址原数据。当源操作数为掩码寄存器时，单次搬出量为掩码寄存器长度（32字节），将掩码寄存器中的数据直接搬出，不支持配置掩码。搬运过程中数据格式与内容保持不变。本接口在Vector Function（__simd_vf__标记的函数）内使用，目的操作数为UB地址。 矢量数据寄存器搬出场景提供以下四种模式： 掩码寄存器搬出场景提供以下三种模式：
约束：非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；dst_align32b/dst起始地址需32字节对齐，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../../../../../runbooks/compilation/reg_load_and_store_use_distinct_dist_enums.md)（`exemplifies`）：AscStorealign 与《LoadDist 错用 DIST_NORM_B32 导致编译失败》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscStorealign》说明将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v1_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。；《AscStorealign》说明将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。。二者在废弃StoreAlign与现行StoreAlign、PostUpdate和原子配置的差异决定UB连续搬出地址及写语义上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v2_deprecated.md)（`related`）：通用 AscStoreAlign 保留连续对齐搬出能力，可用于不依赖旧 v2 特殊签名的迁移。
- [AscStoreAlign](asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《AscStorealign》说明将矢量数据寄存器或掩码寄存器中的数据以32B对齐方式搬出到UB，支持连续、偏移、非连续等多种搬出模式。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [asc_storealign (废弃)](asc_storealign_v5_deprecated.md)（`related`）：若无需 postupdate 的地址更新语义，可改用通用 AscStoreAlign 完成连续对齐搬出。
- [AscStore](asc_store.md)（`same_topic`）：AscStorealign 与《AscStore》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStoreAlign](asc_storealign_v3_deprecated.md)（`same_topic`）：AscStoreAlign 与《AscStorealign》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：AscStorealign 与《AscStoreAlignPostupdate》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStoreUnalign](asc_storeunalign.md)（`same_topic`）：AscStorealign 与《AscStoreUnalign》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStorealignIntlv](asc_storealign_intlv.md)（`same_topic`）：AscStorealignIntlv 与《AscStorealign》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [StoreAlignContinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md)（`same_topic`）：AscStorealign 与《StoreAlignContinuous》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [StoreAlignNoncontinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_align_noncontinuous.md)（`same_topic`）：AscStorealign 与《StoreAlignNoncontinuous》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [reg数据搬出](reg_store.md)（`same_topic`）：AscStorealign 与《reg数据搬出》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
<!-- cannbot:related:end -->
