---
type: API
title: StoreAlignMaskReg
description: 将数据从MaskReg搬运至Unified Buffer，支持普通搬运和PostUpdate扩展搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/StoreAlign_MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# StoreAlignMaskReg

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

StoreAlign能够实现数据从MaskReg搬运至Unified Buffer（UB）。有三类搬运接口
- 普通搬运接口：完成一次搬运后，UB地址不会自动更新，每次迭代需要手动更新地址。
- PostUpdate扩展搬运接口
    - POST_MODE_NORMAL模式：不支持。
    - POST_MODE_UPDATE模式：完成一次搬运后，UB地址会自动更新，每次迭代不需要手动更新地址。

- 使用AddrReg寄存器存储偏移量场景：在每次迭代中，需要先调用CreateAddrReg手动设定地址偏移量，再调用搬运指令。

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；dist: 搬运模式，MaskDist类型。具体参数说明请参考表3 MaskDist参数说明。；dstAddr(输入/输出): 目的操作数，UB起始地址，需要32字节对齐。；mask(输入): 源操作数，类型为MaskReg。；offset(输入): • 当数据类型为AddrReg，为地址偏移寄存器，需要在搬运前调用CreateAddrReg设定地址偏移量，实际搬运UB地址为dstAddr + 寄存器中存储的偏移量。AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束请参考表3 MaskDist参数说明。 • 当数据类型为int32_t，为地址更新步长，单位：字节。offset的对齐约束请参考表3 MaskDist参数说明。根据postMode的取值有两种情况： • POST_MODE_NORMAL：不支持。 • POST_MODE_UPDATE：实际搬运UB起始地址为dstAddr，搬运后执行地址更新 dstAddr += offset。；MaskDist取值: 搬运对齐约束（Byte）；DIST_NORM: VL/8

支持数据类型：b8、b16、b32、b64。

约束：- 位于Unified Buffer的地址约束、offset的对齐约束、AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束与MaskDist有关，具体地址约束
- MaskReg模板参数regTrait只支持RegTraitNumOne。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscStoreAlign](../../../c_api/reg/reg_store/asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《StoreAlignMaskReg》说明将数据从MaskReg搬运至Unified Buffer，支持普通搬运和PostUpdate扩展搬运。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [LoadAlign](../reg_data_load/load_align_mask_reg.md)（`related`）：LoadAlignMaskReg 把 UB 搬入 MaskReg，StoreAlignMaskReg 按相同 MaskDist/PostUpdate/AddrReg 约束反向搬回 UB，构成 MaskReg 数据往返。
- [MaskReg](../register_data_types/mask_reg.md)（`related`）：StoreAlignMaskReg 与《MaskReg》的实质衔接是：MaskReg Store 的对齐/非对齐形态依赖 MaskReg 生成，LoadAlign 是反向搬入，C API StoreAlign 提供同语义入口。
- [MaskGenWithRegTensor](../reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`same_topic`）：StoreAlignMaskReg 与《MaskGenWithRegTensor》的实质衔接是：MaskReg Store 的对齐/非对齐形态依赖 MaskReg 生成，LoadAlign 是反向搬入，C API StoreAlign 提供同语义入口。
- [StoreUnAlignMaskReg](store_un_align_mask_reg.md)（`same_topic`）：StoreUnAlignMaskReg 与《StoreAlignMaskReg》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
<!-- cannbot:related:end -->
