---
type: API
title: StoreAlignNoncontinuous
description: 将数据从RegTensor非连续搬运至Unified Buffer，以DataBlock为单位进行搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/StoreAlign_noncontinuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# StoreAlignNoncontinuous

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

StoreAlign能够实现数据从RegTensor非连续搬运至Unified Buffer（UB），有两类接口
- 普通搬运接口：完成一次搬运后，UB地址不会自动更新，每次迭代需要手动更新地址。
- PostUpdate扩展搬运接口：完成一次搬运后，UB地址会自动更新，每次迭代不需要手动更新地址。

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；dataMode: 非连续对齐场景下的搬运模式，DataCopyMode类型。具体参数说明请参考表3 DataCopyMode参数说明。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；U: 源操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstAddr(输入/输出): 目的操作数，UB起始地址，需要32字节对齐。；srcReg(输入): 源操作数，类型为RegTensor。；dataBlockStride(输入): 单条指令一次搬运8个DataBlock，该参数表示相邻DataBlock间的间隔（前面一个DataBlock的头与后面DataBlock的头的间隔），单位。

支持数据类型：b8、b16、b32。

约束：- 位于Unified Buffer的地址必须32字节对齐。
- RegTensor模板参数regTrait只支持RegTraitNumOne。
- repeatStride * 32B / sizeof(T)需要32字节对齐。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《StoreAlignNoncontinuous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：StoreAlignNoncontinuous 与《连续非对齐场景优化》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [非连续搬运场景减少搬运次数](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_non_contiguous_transfer.md)（`explains`）：StoreAlignNoncontinuous 与《非连续搬运场景减少搬运次数》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [AscStoreAlign](../../../c_api/reg/reg_store/asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《StoreAlignNoncontinuous》说明将数据从RegTensor非连续搬运至Unified Buffer，以DataBlock为单位进行搬运。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [AscStoreAlignPostupdate](../../../c_api/reg/reg_store/asc_storealign_postupdate.md)（`same_topic`）：StoreAlignNoncontinuous 与《AscStoreAlignPostupdate》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [AscStorealign](../../../c_api/reg/reg_store/asc_storealign.md)（`same_topic`）：AscStorealign 与《StoreAlignNoncontinuous》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [LoadAlign](../reg_data_load/load_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《LoadAlign》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [Reg数据搬出](reg_data_store.md)（`same_topic`）：StoreAlignNoncontinuous 与《Reg数据搬出》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [StoreAlignContinuous](store_align_continuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《StoreAlignContinuous》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [StoreUnAlignContinuous](store_un_align_continuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《StoreUnAlignContinuous》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
<!-- cannbot:related:end -->
