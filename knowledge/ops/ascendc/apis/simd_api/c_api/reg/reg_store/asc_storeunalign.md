---
type: API
title: AscStoreUnalign
description: 从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreUnalign

reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口使用uint32_t作为存储偏移量，不改变源操作数在UB上的地址，每次循环的调用都需要用户手动更新目的操作数在UB上的地址。
函数原型：void asc_storeunalign(__ubuf__ int8_t* dst, vector_store_unalign& src0, vector_int8_t src1, uint32_t count)
约束：该接口中的dst不需要32B对齐。；调用该接口之后，需要调用asc_storeunalign_post处理非对齐搬出的尾块。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“连续非对齐场景优化”明确连续非对齐搬运场景的性能优化建议与接口介绍。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`related`）：AscStoreUnalign 负责非对齐搬出的主体数据，AscStoreUnalignPost 负责用暂存寄存器完成最终跨边界尾部，两者按阶段配合。
- [StoreUnAlignMaskReg](../../../basic_api/reg_vector_compute/reg_data_store/store_un_align_mask_reg.md)（`related`）：StoreUnAlignMaskReg 与《AscStoreUnalign》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscStoreUnalign》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscStoreUnalignPost](asc_storeunalign_post.md)（`same_topic`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“AscStoreUnalignPost”明确从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，将非对齐寄存器中暂存的尾块搬出到UB，需在asc_storeunalign或asc_storeunalign_postupdate之后调用。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [AscStoreUnalignPostupdate](asc_storeunalign_postupdate.md)（`same_topic`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“AscStoreUnalignPostupdate”明确从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStorealign 与《AscStoreUnalign》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [Store](../../../basic_api/reg_vector_compute/reg_data_store/store.md)（`same_topic`）：C++ Store 封装非对齐 Reg→UB 搬出，C API AscStoreUnalign 是同一机制的对应入口。
- [StoreUnAlignContinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_un_align_continuous.md)（`same_topic`）：AscStoreUnalign 是 C API 下相同的连续非 32B 对齐搬出，补充手动偏移和尾块 finalize 契约。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalign正文界定“从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
