---
type: API
title: StoreUnAlignMaskReg
description: 将数据从MaskReg连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/StoreUnAlign_MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# StoreUnAlignMaskReg

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

StoreUnAlign能够实现数据从MaskReg连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；dstAddr(输入/输出): 目的操作数，UB起始地址，不需要32字节对齐。b16数据类型时需要16字节对齐，b32数据类型时需要8字节对齐。；mask(输入): 源操作数，类型为MaskReg。；ureg(输入/输出): 非对齐寄存器，UnalignRegForStore类型，用于存储非32B对齐的数据，寄存器大小为32字节。；postUpdateStride(输入): 地址更新步长，uint32_t类型，单位：元素个数。根据postMode的取值有两种情况： &bull; POST_MODE_NORMAL：不支持。 &b。

支持数据类型：b16、b32。

约束：- 数据类型为b16时，位于Unified Buffer的地址必须16字节对齐，搬运完成后UB地址按16B偏移量更新，不需要手动更新地址。
- 数据类型为b32时，位于Unified Buffer的地址必须8字节对齐，搬运完成后UB地址按8B偏移量更新，不需要手动更新地址。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalignInit](../../../c_api/reg/system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：StoreUnAlignMaskReg 与《AscSqueezeAndStoreunalignInit》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [AscStoreUnalign](../../../c_api/reg/reg_store/asc_storeunalign.md)（`related`）：StoreUnAlignMaskReg 与《AscStoreUnalign》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [UnalignRegForLoadAndUnalignRegForStore](../register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《StoreUnAlignMaskReg》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [LoadUnAlign](../reg_data_load/load_un_align_continuous.md)（`same_topic`）：StoreUnAlignMaskReg 与《LoadUnAlign》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [MaskGenWithRegTensor](../reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`same_topic`）：StoreUnAlignMaskReg 与《MaskGenWithRegTensor》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [MaskReg](../register_data_types/mask_reg.md)（`same_topic`）：MaskReg 与《StoreUnAlignMaskReg》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [StoreAlignMaskReg](store_align_mask_reg.md)（`same_topic`）：StoreUnAlignMaskReg 与《StoreAlignMaskReg》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
<!-- cannbot:related:end -->
