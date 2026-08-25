---
type: API
title: AscStoreUnalignPost
description: 已废弃接口。从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，不指定偏移量，将非对齐寄存器中暂存的尾块搬出到UB。请使用asc_squeeze_and_storeunalign_finalize替代。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_post_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStoreUnalignPost

该接口已废弃。请使用asc_squeeze_and_storeunalign_finalize实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的尾块场景。 需要先调用下列接口之一后，再调用本接口。
函数原型：void asc_storeunalign_post(__ubuf__ int8_t* dst, vector_store_unalign src)
约束：该接口中的dst不需要32B对齐，但数据类型为T的dst需要sizeof(T) Byte对齐。；调用本接口之前，需要调用asc_storeunalign_postupdate接口，且本接口与前序接口的非对齐寄存器要保持一致。；需要保证目的操作数的地址加上offset对应的偏移地址，结果等于数据搬运的结束地址，具体见调用示例。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreUnalign](asc_storeunalign.md)（`related`）：AscStoreUnalign 负责非对齐搬出的主体数据，AscStoreUnalignPost 负责用暂存寄存器完成最终跨边界尾部，两者按阶段配合。
- [AscStoreUnalignPostupdate](asc_storeunalign_postupdate.md)（`related`）：AscStoreUnalignPostupdate 在非对齐搬出时更新源寄存器或地址状态，与 Post 收尾接口共同支持循环式连续写回。
- [reg数据搬出](reg_store.md)（`related`）：reg 数据搬出总览把 StoreUnalign/Post/Postupdate 组织为一组，说明它们与对齐、Scatter、Pack 等搬出方式的选择边界。
- [AscSqueezeAndStoreunalignFinalize](asc_squeeze_and_storeunalign_finalize.md)（`same_topic`）：废弃 AscStoreUnalignPost 正文明确指定 AscSqueezeAndStoreunalignFinalize 为替代接口；二者都负责把非对齐寄存器暂存的尾块最终写入 UB。
- [AscStoreUnalignPost](asc_storeunalign_post.md)（`same_topic`）：当前 AscStoreUnalignPost 是废弃同名接口的直接承接者，保留非对齐连续搬出并处理末尾暂存数据。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscStoreUnalignPost正文界定“已废弃接口。从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，不指定偏移量，将非对齐寄存器中暂存的尾块搬出到UB。请使用asc_squeeze_and_storeunalign_finalize替代”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
