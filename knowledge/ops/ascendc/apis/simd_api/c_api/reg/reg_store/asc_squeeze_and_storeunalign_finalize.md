---
type: API
title: AscSqueezeAndStoreunalignFinalize
description: 配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_squeeze_and_storeunalign_finalize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSqueezeAndStoreunalignFinalize

reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。 搬运原理如下： 记目的操作数的起始地址为dst_start，结束地址为dst_end，尾块元素个数为unalign_count = (dst_end - dst_end / 32  32) / sizeof(T)。则搬运的数据会分为两部分，分别是：
函数原型：void asc_squeeze_and_storeunalign_finalize(__ubuf__ int8_t* dst, vector_store_unalign src)
约束：该接口中的dst不需要32B对齐，需要和asc_squeeze_and_storeunalign配置的目的操作数地址及非对齐寄存器保持一致。；需要保证目的操作数的地址写入非对齐寄存器中的数据后不越过UB可用容量上限，否则触发写越界异常。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](asc_squeeze_and_storeunalign.md)（`related`）：Finalize 必须在 AscSqueezeAndStoreunalign 过滤并累计非对齐数据后调用，才能把暂存在寄存器中的尾块写出。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：Init 在首次 squeeze-store 前清零 AR 偏移，和 Finalize 分别闭合该状态机的开始与结束。
- [asc_storeunalign_postupdate](asc_storeunalign_postupdate_deprecated.md)（`related`）：AscSqueezeAndStoreunalignFinalize说明配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：AscSqueezeAndStoreunalignFinalize说明配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
- [AscSqueezeV2](../compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：AscSqueezeAndStoreunalignFinalize说明配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
- [AscSqueezeWithStatus](../compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalignFinalize》补充：配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`same_topic`）：废弃 AscStoreUnalignPost 正文明确指定 AscSqueezeAndStoreunalignFinalize 为替代接口；二者都负责把非对齐寄存器暂存的尾块最终写入 UB。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalignFinalize正文界定“配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
