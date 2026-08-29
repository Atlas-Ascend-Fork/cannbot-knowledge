---
type: API
title: StoreUnAlignContinuous
description: 将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/StoreUnAlign_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# StoreUnAlignContinuous

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

为提升对不规则内存地址的处理能力，Reg矢量计算支持在数据搬运过程中对非32字节对齐的地址进行访问，降低非对齐访问带来的性能开销。StoreUnAlign能够实现数据从RegTensor连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。

非对齐搬运接口有：PostUpdate扩展搬运接口、使用AddrReg寄存器存储偏移量接口、使用AR寄存器存储偏移量接口。

RegTensor的模板参数regTrait支持RegTraitNumOne及RegTraitNumTwo。
非对齐搬出原理

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；U: 源操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstAddr(输入/输出): 目的操作数，UB起始地址，不需要32字节对齐。；srcReg(输入): 源操作数，类型为RegTensor。；ureg(输入/输出): 非对齐寄存器，UnalignRegForStore类型，用于存储非32字节对齐的数据，寄存器大小为32字节。；postUpdateStride(输入): 地址更新步长，uint32_t类型，单位：元素个数。根据postMode的取值有两种情况： &bull; POST_MODE_NORMAL：不支持。 &b。

支持数据类型：b8、b16、b32、b64。

约束：- StoreUnAlign与StoreUnAlignPost接口需要组合使用。
- 对于使用AR寄存器存储偏移量接口
    - 当Squeeze接口的模板参数store配置为STORE_REG时，必须保证Squeeze接口和StoreUnAlign交替使用。
    - 在调用计算前需要调用ClearSpr接口，将AR寄存器清零。

- 当RegTensor模板参数RegTrait为RegTraitNumOne和RegTraitNumTwo时，支持情况

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Squeeze](../compare_and_select/squeeze.md)（`related`）：“StoreUnAlign会自动从AR寄存器读取有效字节数作为地址偏移”说明 Squeeze 的 STORE_REG 输出直接驱动连续非对齐写址；“必须保证Squeeze接口和StoreUnAlign交替使用”给出消费该 AR 状态时的硬件调用顺序。
- [StoreUnAlignMaskReg](store_un_align_mask_reg.md)（`same_topic`）：StoreUnAlign能够实现数据从MaskReg连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。；StoreUnAlign能够实现数据从RegTensor连续搬运至非对齐Unified Buffer（UB），利用非对齐寄存器UnalignRegForStore作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。。两卡描述同一 StoreUnAlign 非对齐连续搬运契约，并共享 UnalignRegForStore 跨边界暂存机制；差别仅在源操作数是 MaskReg 还是 RegTensor。
<!-- cannbot:related:end -->
