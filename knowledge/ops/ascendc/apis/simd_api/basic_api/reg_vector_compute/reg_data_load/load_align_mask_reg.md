---
type: API
title: LoadAlign
description: 将数据从UB搬运至MaskReg，支持普通搬运、PostUpdate扩展搬运和AddrReg偏移量三种接口，可通过MaskDist配置上采样、下采样等数据分布模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/LoadAlign_MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# LoadAlign

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

LoadAlign能够实现数据从Unified Buffer（UB）搬运至MaskReg。有三类搬运接口
- 普通搬运接口：完成一次搬运后，UB地址不会自动更新，每次迭代需要手动更新地址。
- PostUpdate扩展搬运接口：有两种模式选择，具体介绍
    - POST_MODE_NORMAL模式：不支持。
    - POST_MODE_UPDATE模式：完成一次搬运后，UB地址会自动更新，每次迭代不需要手动更新地址。

- 使用AddrReg寄存器存储偏移量场景：在每次迭代中，需要先调用CreateAddrReg手动设定地址偏移量，再调用搬运指令。

数据搬入时，可以通过模板参数配置搬运的数据分布模式，能够实现上采样、下采样等功能，分布模式具体介绍

图1、图2、图3

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；dist: 搬运模式，MaskDist类型。具体参数说明请参考表3 MaskDist参数说明。；mask(输出): 目的操作数，类型为MaskReg。；srcAddr(输入/输出): 源操作数，UB起始地址。；offset(输入): • 当数据类型为AddrReg，为地址偏移寄存器，需要在搬运前调用CreateAddrReg设定地址偏移量，实际搬运UB地址为srcAddr + 寄存器中存储的偏移量。AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束请参考表3 MaskDist参数说明。 • 当数据类型为int32_t，为地址更新步长，单位：字节。offset的对齐约束请参考表3 MaskDist参数说明。根据postMode的取值有两种情况： • POST_MODE_NORMAL：不支持。 • POST_MODE_UPDATE：实际搬运UB起始地址为srcAddr，搬运后执行地址更新 srcAddr += offset。；MaskDist取值: 搬运对齐约束（Byte）；DIST_NORM: VL/8

支持数据类型：b8、b16、b32、b64。

约束：- 位于Unified Buffer的地址约束、offset的对齐约束、AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束与分布模式MaskDist有关，具体地址约束
- MaskReg模板参数regTrait只支持RegTraitNumOne。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《LoadAlign》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [Reg LoadAlign 不接受 const __ubuf__ 指针](../../../../../runbooks/compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`exemplifies`）：Runbook 实测两参数 Reg LoadAlign 不接受 const __ubuf__ 指针，并追到 asc_vf_call 包装边界；这是调用该搬入族时的直接编译诊断。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《LoadAlign》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [AddrReg](../register_data_types/addr_reg.md)（`related`）：选择 AddrReg 重载时必须先创建并配置多维地址偏移，LoadAlign 再按该偏移访问 UB；AddrReg 是该寻址模式的前置对象。
- [AscLoadalign](../../../c_api/reg/reg_load/asc_loadalign.md)（`related`）：AscLoadalign 的 C API 可把 32B 对齐 UB 搬入矢量寄存器或 MaskReg，并覆盖立即数、AddrReg 与非连续模式，是该基础 API 的 C 层映射。
- [AscLoadalignPostupdate](../../../c_api/reg/reg_load/asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《LoadAlign》明确提供“将数据从UB搬运至MaskReg，支持普通搬运、PostUpdate扩展搬运和AddrReg偏移量三种接口，可通过MaskDist配置上采样、下采样等数据分布模式。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [MaskGenWithRegTensor](mask_gen_with_reg_tensor_mask_reg.md)（`related`）：MaskGen 从 RegTensor 的选定数据块生成 MaskReg，LoadAlignMaskReg 从 UB 搬入 MaskReg；二者按掩码来源是寄存器数据还是内存数据选用。
- [StoreAlignMaskReg](../reg_data_store/store_align_mask_reg.md)（`related`）：LoadAlignMaskReg 把 UB 搬入 MaskReg，StoreAlignMaskReg 按相同 MaskDist/PostUpdate/AddrReg 约束反向搬回 UB，构成 MaskReg 数据往返。
- [LoadAlign](load_align_noncontinuous.md)（`same_topic`）：LoadAlign 与《LoadAlign》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [MaskReg](../register_data_types/mask_reg.md)（`same_topic`）：MaskReg 与《LoadAlign》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
<!-- cannbot:related:end -->
