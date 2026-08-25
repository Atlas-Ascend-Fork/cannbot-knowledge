---
type: API
title: StoreAlignContinuous
description: 将数据从RegTensor连续搬运至Unified Buffer，支持单搬出和双搬出模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/StoreAlign_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# StoreAlignContinuous

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

StoreAlign能够实现数据从RegTensor连续搬运至Unified Buffer（UB），支持单搬出模式和双搬出模式
- 单搬出模式：将一个RegTensor（VL）中的VL数据量搬出至UB。
- 双搬出模式：将两个RegTensor(2*VL)的数据交错搬出至UB，偶数索引和奇数索引的元素分别来自两个RegTensor。

连续对齐搬运有三类接口：普通搬运接口、PostUpdate扩展搬运接口、使用AddrReg寄存器存储偏移量接口。

RegTensor的模板参数regTrait支持RegTraitNumOne及RegTraitNumTwo。
数据搬出时，可以通过模板参数配置搬运的数据分布模式，能够实现压缩、只搬出第一个元素等功能，分布模式具体介绍

连续对齐搬入/搬出的三类搬运接口在迭代内调用方式

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；dist: 搬运模式，StoreDist类型。具体参数说明请参考表3 StoreDist参数说明（单搬出模式）。；U: 源操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dstAddr(输入/输出): 目的操作数，UB起始地址。；srcReg(输入): 源操作数，类型为RegTensor。；postUpdateStride(输入): 地址更新步长，int32_t类型，单位：元素个数。postUpdateStride * sizeof(T)的对齐约束请参考表3 StoreDist参数说明（单搬出模式）。根据postMode的取值有两种情况： • POST_MODE_NORMAL：不支持。 • POST_MODE_UPDATE：实际搬运UB起始地址为dstAddr，搬运后执行地址更新dstAddr += postUpdateStride。；offset(输入): 地址偏移寄存器，AddrReg类型。需要在搬运前调用CreateAddrReg设定地址偏移量，实际搬运UB地址为dstAddr + 寄存器中存储的偏移量。AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束请参考表3 StoreDist参数说明（单搬出模式）。

支持数据类型：b8、b16、b32、b64。

约束：- 位于Unified Buffer的地址约束、postUpdateStride * sizeof(T)的对齐约束、AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束与分布模式StoreDist有关，具体地址约束
- 当RegTrait为RegTraitNumOne时，单搬出正常模式（DIST_NORM）下，若目的UB的剩余空间不足256B，需要配置mask，保证搬出的有效元素数据量不大于UB剩余空间，且UB剩余空间不得小于32B。
- 单搬出模式：b64数据类型只支持StoreDist中的DIST_NORM和DIST_PACK_B64模式。
- 当RegTensor模板参数RegTrait为RegTraitNumOne和RegTraitNumTwo时，支持情况

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《StoreAlignContinuous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：失真组合的写回端直接调用 Reg《StoreAlignContinuous》语义的 StoreAlign，把 Cast 后寄存器按指定 StoreDist 写入 FP32 UB 中间缓冲。
- [AscStoreAlign](../../../c_api/reg/reg_store/asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《StoreAlignContinuous》说明将数据从RegTensor连续搬运至Unified Buffer，支持单搬出和双搬出模式。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [LoadAlign](../reg_data_load/load_align_continuous.md)（`related`）：LoadAlignContinuous 是该连续对齐 Store 的生产侧对偶，二者共享分布模式和单/双寄存器布局，便于构造完整 Reg 搬运链。
- [StoreUnAlignContinuous](store_un_align_continuous.md)（`related`）：StoreAlignContinuous 是目的 UB 32B 对齐时的替代路径；两者的选择由地址对齐和跨边界暂存需求决定。
- [AscStoreAlign](../../../c_api/reg/reg_store/asc_storealign_v3_deprecated.md)（`same_topic`）：AscStoreAlign 与《StoreAlignContinuous》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [AscStorealign](../../../c_api/reg/reg_store/asc_storealign.md)（`same_topic`）：AscStorealign 与《StoreAlignContinuous》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStorealignIntlv](../../../c_api/reg/reg_store/asc_storealign_intlv.md)（`same_topic`）：AscStorealignIntlv 与《StoreAlignContinuous》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [StoreAlignNoncontinuous](store_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《StoreAlignContinuous》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
<!-- cannbot:related:end -->
