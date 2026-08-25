---
type: API
title: AscSqueezeAndStoreunalign
description: 从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_squeeze_and_storeunalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSqueezeAndStoreunalign

reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的场景。 本接口将输入矢量数据寄存器src1中被掩码squeeze_mask选择的有效元素依次复制到矢量数据寄存器dst，有效元素在dst上连续排列，dst中后续非有效元素置0。若AR寄存器（用于累加已搬出的有效数据量）中累加了前序asc_squeeze_and_storeunalign指令的有效元素总数据量，则将dst中有效数据写入dst_addr + AR寄存器数据量的地址，并将本次执行的有效数据量大小（以字节为单位）累加进AR寄存器。如调用示例所示，多次连续调用本接口时，若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。
函数原型：void asc_squeeze_and_storeunalign(__ubuf__ int8_t* dst_addr, vector_int8_t dst, vector_store_unalign& src0, vector_int8_t src1, vector_bool squeeze_mask)
约束：该接口中的dst_addr不需要32B对齐。；调用本接口后，需要调用asc_squeeze_and_storeunalign_finalize接口进行收尾。；首次调用本接口前或不想基于AR寄存器偏移时，需要调用asc_squeeze_and_storeunalign_init接口清空AR寄存器中的数据。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscGetSqueezeStatus](../../sys_var/asc_get_squeeze_status.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeAndStoreunalign》说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueeze](../compare_and_select/asc_squeeze.md)（`related`）：AscSqueeze 只在 Reg 中压紧且不保存有效数，Storeunalign 变体同时用 AR 累计长度并连续写 UB，适合需要跨调用非对齐搬出的路径。
- [AscSqueezeAndStoreunalignFinalize](asc_squeeze_and_storeunalign_finalize.md)（`related`）：Finalize 必须在 AscSqueezeAndStoreunalign 过滤并累计非对齐数据后调用，才能把暂存在寄存器中的尾块写出。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：AscSqueezeAndStoreunalign 与《UnalignRegForLoadAndUnalignRegForStore》的实质衔接是：AscSqueezeAndStoreunalign 必须先 Init 清 AR、可多次压紧并自动推进地址、最后 Finalize；旧 SqueezeWithStatus/GetSqueezeStatus 路径解释迁移前的长度状态。
- [asc_storeunalign_postupdate](asc_storeunalign_postupdate_deprecated.md)（`related`）：AscSqueezeAndStoreunalign说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理；对asc_storeunalign_postupdate而言，废弃 postupdate 接口的直接迁移目标保留自动地址更新；Squeeze 路线则额外要求 init/finalize 和 AR 累加管理。
- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：AscSqueezeAndStoreunalign说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`same_topic`）：AscSqueezeAndStoreunalign 与《AscSqueezeAndStoreunalignInit》的实质衔接是：AscSqueezeAndStoreunalign 必须先 Init 清 AR、可多次压紧并自动推进地址、最后 Finalize；旧 SqueezeWithStatus/GetSqueezeStatus 路径解释迁移前的长度状态。
- [AscSqueezeV2](../compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：AscSqueezeAndStoreunalign 与《AscSqueezeV2》的实质衔接是：AscSqueezeAndStoreunalign 必须先 Init 清 AR、可多次压紧并自动推进地址、最后 Finalize；旧 SqueezeWithStatus/GetSqueezeStatus 路径解释迁移前的长度状态。
- [AscSqueezeWithStatus](../compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalign》补充：从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalign正文界定“从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
