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

- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：连续非对齐场景优化 的核心契约是“连续非对齐搬运场景的性能优化建议与接口介绍”；StoreUnAlignContinuous 补充“将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据”。
- [LoadUnAlign](../reg_data_load/load_un_align_continuous.md)（`related`）：LoadUnAlign 是非对齐连续 Store 的读侧对偶，二者组合可处理 UB 非对齐的寄存器往返。
- [Squeeze](../compare_and_select/squeeze.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《StoreUnAlignContinuous》补充：将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据。
- [StoreAlignContinuous](store_align_continuous.md)（`related`）：StoreAlignContinuous 是目的 UB 32B 对齐时的替代路径；两者的选择由地址对齐和跨边界暂存需求决定。
- [UnalignRegForLoadAndUnalignRegForStore](../register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《StoreUnAlignContinuous》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscStoreUnalign](../../../c_api/reg/reg_store/asc_storeunalign.md)（`same_topic`）：AscStoreUnalign 是 C API 下相同的连续非 32B 对齐搬出，补充手动偏移和尾块 finalize 契约。
- [Store](store.md)（`same_topic`）：Store 是连续非对齐搬出的便捷封装，底层语义对应 StoreUnAlign 连续接口。
- [StoreAlignNoncontinuous](store_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《StoreUnAlignContinuous》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [reg数据搬出](../../../c_api/reg/reg_store/reg_store.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；StoreUnAlignContinuous正文说明“将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
<!-- cannbot:related:end -->
