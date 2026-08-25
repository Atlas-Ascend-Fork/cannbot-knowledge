---
type: API
title: AscStoreUnalignPostupdate
description: 从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreUnalignPostupdate

reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。
函数原型：void asc_storeunalign_postupdate(__ubuf__ uint16_t*& dst, vector_store_unalign& src0, vector_bool src1)
约束：该接口中的dst不需要32B对齐。；使用uint32_t作为存储偏移量时，本接口应与asc_storeunalign_post_postupdate接口配合使用。asc_storeunalign_post_postupdate接口用于处理该场景下非对齐搬出的尾块。；使用addr_reg作为存储偏移量时，本接口应与asc_storeunalign_post接口配合使用。asc_storeunalign_post接口用于处理该场景下非对齐搬出的尾块。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreUnalignPost](asc_storeunalign_post.md)（`related`）：PostUpdate 版本在生成主体状态时自动更新地址；其 offset 类型决定随后应选择哪一种 Post 尾处理。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`related`）：AscStoreUnalignPostupdate 在非对齐搬出时更新源寄存器或地址状态，与 Post 收尾接口共同支持循环式连续写回。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：PostUpdate store 消费更新后的 AddrReg，展示实际下游。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscStoreUnalignPostupdate》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscStoreUnalign](asc_storeunalign.md)（`same_topic`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“AscStoreUnalignPostupdate”明确从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalignPostupdate正文界定“从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [asc_storeunalign_postupdate](asc_storeunalign_postupdate_deprecated.md)（`same_topic`）：AscStoreUnalignPostupdate说明从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
<!-- cannbot:related:end -->
