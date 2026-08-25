---
type: API
title: asc_storeunalign_postupdate
description: 该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。
  该接口每调用一次接口会更新目的操作数在UB上的地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_postupdate_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_storeunalign_postupdate

该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB上的地址。
函数原型：void asc_storeunalign_postupdate(__ubuf__ int8_t* dst, vector_store_unalign& src0, vector_int8_t src1)
约束：该接口中的dst不需要32B对齐。；本接口应该配合asc_storeunalign_post接口一起使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](asc_squeeze_and_storeunalign.md)（`related`）：AscSqueezeAndStoreunalign说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
- [AscSqueezeAndStoreunalignFinalize](asc_squeeze_and_storeunalign_finalize.md)（`related`）：AscSqueezeAndStoreunalignFinalize说明配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
- [AscStoreUnalignPostupdate](asc_storeunalign_postupdate.md)（`same_topic`）：AscStoreUnalignPostupdate说明从矢量数据寄存器或掩码寄存器连续非32B对齐搬出到UB，每调用一次自动更新目的地址，支持uint32_t或addr_reg作为存储偏移量；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；asc_storeunalign_postupdate正文界定“该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器或掩码寄存器连续非32B对齐的起始地址连续搬出到UB的场景。 该接口每调用一次接口会更新目的操作数在UB”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
