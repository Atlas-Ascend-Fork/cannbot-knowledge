---
type: API
title: LoadAlign
description: 将数据从UB非连续搬运至RegTensor，以DataBlock为单位进行搬运，支持普通搬运和PostUpdate扩展搬运两类接口，可通过mask控制有效DataBlock。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/LoadAlign_noncontinuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# LoadAlign

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

LoadAlign能够实现数据从Unified Buffer（UB）非连续搬运至RegTensor，有两类接口
- 普通搬运接口：完成一次搬运后，UB地址不会自动更新，每次迭代需要手动更新地址。
- PostUpdate扩展搬运接口：完成一次搬运后，UB地址会自动更新，每次迭代不需要手动更新地址。

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；dataMode: 非连续对齐场景下的搬运模式，DataCopyMode类型。表3 DataCopyMode参数说明。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；U: 目的操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；srcAddr(输入/输出): 源操作数，UB起始地址，需要32字节对齐。；dataBlockStride(输入): 单条指令一次搬运8个DataBlock，该参数表示相邻DataBlock间的间隔（前面一个DataBlock的头与后面DataBlock的头的间隔），单位：DataBlock（32B）。 注：当dataBlockStride=0时，表示重复搬入第一个DataBlock。

支持数据类型：b8、b16、b32。

约束：- 位于Unified Buffer的地址必须32字节对齐。
- RegTensor模板参数regTrait只支持RegTraitNumOne。
- repeatStride * 32B / sizeof(T)需要32字节对齐。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《LoadAlign》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《LoadAlign》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [Reg LoadAlign 不接受 const __ubuf__ 指针](../../../../../runbooks/compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`exemplifies`）：LoadAlign 与《Reg LoadAlign 不接受 const __ubuf__ 指针》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [AscLoadalign](../../../c_api/reg/reg_load/asc_loadalign.md)（`related`）：LoadAlign 与《AscLoadalign》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [LoadAlign](load_align_continuous.md)（`same_topic`）：LoadAlign 与《LoadAlign》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [LoadAlign](load_align_mask_reg.md)（`same_topic`）：LoadAlign 与《LoadAlign》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [StoreAlignNoncontinuous](../reg_data_store/store_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《LoadAlign》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
<!-- cannbot:related:end -->
