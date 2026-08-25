---
type: API
title: reg数据搬出
description: 寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/reg_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# reg数据搬出

寄存器侧数据搬出接口将数据从矢量数据寄存器存储到Unified Buffer。基础接口含asc_store和asc_storeunalign及其post/postupdate变体处理非对齐存储。
asc_storealign及其变体支持对齐存储及多种数据变换：1st（首次）、intlv（交织）、pack（打包）、pack_quarter（四分之一打包）等，postupdate变体支持地址寄存器后更新。asc_scatter提供分散式存储，asc_squeeze_and_storeunalign结合解压与非对齐存储。asc_storealign v1-v5及部分scatter/storeunalign接口已废弃。

<!-- cannbot:related:start -->
## 相关

- [RoPE DIST_INTLV_B16 store mask 致零值](../../../../../runbooks/precision/rope_dist_intlv_b16_store_mask.md)（`exemplifies`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；RoPE DIST_INTLV_B16 store mask 致零值正文说明“MLA 融合算子 rms_norm_rope_k_store_kv_cache（dav-3510/Ascend950/CANN 9.1.0）的 DoRope64 用 DIST_INTLV_B16 interleave store 把 even/odd 配对 RoPE 结果交错写回”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；fp32 UB 非 VL 拷贝须用带掩码 Reg正文说明“fp32 UB 局部 DataCopy 在非 vector-length 元素数上产生轴相关错误；使用 UpdateMask 的 Reg load/store 复制尾块”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
- [AscStoreAlign](asc_storealign_v1_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。；《reg数据搬出》说明寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。。二者在废弃StoreAlign与现行StoreAlign、PostUpdate和原子配置的差异决定UB连续搬出地址及写语义上存在可执行的直接衔接。
- [AscStoreAlign](asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《reg数据搬出》说明寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [AscStoreAlignPackQuarter](asc_storealign_pack_quarter.md)（`related`）：《AscStoreAlignPackQuarter》说明从矢量数据寄存器压缩搬出到UB，根据mask将src有效元素的低8bits数据连续存储于dst_align32b中，支持b32类型。支持Post Update模式，调用后自动更新目的操作数地址。；《reg数据搬出》说明寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。。二者在PackQuarter搬出把b32低8位压紧写入UB；PostUpdate、PACK搬出和高低位压缩接口决定地址与布局上存在可执行的直接衔接。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`related`）：AscStoreAlignPostupdate 与《reg数据搬出》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStoreUnalignPost](asc_storeunalign_post.md)（`related`）：RegStore 总览解释对齐、非对齐和 postupdate 存储族，给出 AscStoreUnalignPost 在完整写回流程中的位置。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`related`）：reg 数据搬出总览把 StoreUnalign/Post/Postupdate 组织为一组，说明它们与对齐、Scatter、Pack 等搬出方式的选择边界。
- [AscStorealign1stPostupdate](asc_storealign_1st_postupdate.md)（`related`）：AscStorealign1stPostupdate 与《reg数据搬出》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`related`）：AscStorealignPackPostupdate 与《reg数据搬出》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStorealign 与《reg数据搬出》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStorealignIntlv](asc_storealign_intlv.md)（`same_topic`）：AscStorealignIntlv 与《reg数据搬出》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [Reg数据搬出](../../../basic_api/reg_vector_compute/reg_data_store/reg_data_store.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；Reg数据搬出正文说明“Reg数据搬出接口索引页，涵盖StoreAlign连续/非连续、StoreUnAlign、MaskReg搬出、Scatter离散搬出及Store”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
- [Store](../../../basic_api/reg_vector_compute/reg_data_store/store.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；Store正文说明“从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
- [StoreUnAlignContinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_un_align_continuous.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；StoreUnAlignContinuous正文说明“将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
<!-- cannbot:related:end -->
