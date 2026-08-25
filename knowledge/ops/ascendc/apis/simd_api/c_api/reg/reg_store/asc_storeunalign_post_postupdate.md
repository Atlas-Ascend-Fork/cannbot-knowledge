---
type: API
title: asc_storeunalign_post_postupdate
description: 从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，每调用一次自动更新目的地址，将非对齐寄存器中暂存的尾块搬出到UB，需在asc_storeunalign_postupdate之后调用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_post_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_storeunalign_post_postupdate

reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的尾块场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。 需要先调用下列接口后，再调用本接口。
函数原型：void asc_storeunalign_post_postupdate(__ubuf__  int8_t*& dst, vector_store_unalign src, int32_t offset)
约束：该接口中的dst不需要32B对齐，但数据类型为T的dst需要sizeof(T) Byte对齐。；调用本接口之前，需要调用asc_storeunalign_postupdate使用uint32_t作为存储偏移量的接口，且本接口与前序接口的非对齐寄存器要保持一致。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](asc_squeeze_and_storeunalign.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalign正文界定“从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [AscSqueezeAndStoreunalignFinalize](asc_squeeze_and_storeunalign_finalize.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalignFinalize正文界定“配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalignInit正文界定“对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [AscStoreUnalign](asc_storeunalign.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalign正文界定“从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [AscStoreUnalignPost](asc_storeunalign_post.md)（`same_topic`）：AscStoreUnalignPost 与 post_postupdate 都完成非对齐连续搬出的尾块收尾；后者在相同收尾合同上自动推进目的地址，前者由调用方提供偏移。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalignPost正文界定“已废弃接口。从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，不指定偏移量，将非对齐寄存器中暂存的尾块搬出到UB。请使用asc_squeeze_and_storeunalign_finalize替代”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [AscStoreUnalignPostupdate](asc_storeunalign_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalignPostupdate正文界定“从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
- [asc_storeunalign_postupdate](asc_storeunalign_postupdate_deprecated.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；asc_storeunalign_postupdate正文界定“该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
