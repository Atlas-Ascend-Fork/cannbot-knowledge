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

- [StoreUnAlignContinuous](store_un_align_continuous.md)（`same_topic`）：StoreUnAlign能够实现数据从MaskReg连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。；StoreUnAlign能够实现数据从RegTensor连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。。两卡描述同一 StoreUnAlign 非对齐连续搬运契约，并共享 UnalignRegForStore 跨边界暂存机制；差别仅在源操作数是 MaskReg 还是 RegTensor。
<!-- cannbot:related:end -->
