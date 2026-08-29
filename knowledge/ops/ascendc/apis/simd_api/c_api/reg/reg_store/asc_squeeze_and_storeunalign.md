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

- [AscSqueezeAndStoreunalignFinalize](asc_squeeze_and_storeunalign_finalize.md)（`related`）：约束：该接口中的dst_addr不需要32B对齐。；调用本接口后，需要调用asc_squeeze_and_storeunalign_finalize接口进行收尾。；首次调用本接口前或不想基于AR寄存器偏移时，需要调用asc_squeeze_and_storeunalign_init接口清空AR寄存器中的数据。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。 搬运原理如下： 记目的操作数的起始地址为dst_start，结束地址为dst_end，尾块元素个数为unalign_count = (dst_end - dst_end / 32 32) / sizeof(T)。则搬运的数据会分为两部分，分别是：。主接口的调用约束明确要求随后执行 finalize，目标接口专门把非对齐寄存器中剩余尾块搬到 UB，因此二者形成连续非对齐筛选存储的主体与收尾调用链。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：Init 卡规定“在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。”；store API说明“若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。”。清零建立本轮连续搬出的偏移基点。
- [AscSqueezeV2](../compare_and_select/asc_squeeze_deprecated.md)（`related`）：该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的场景。 本接口将输入矢量数据寄存器src1中被掩码squeeze_mask选择的有效元素依次复制到矢量数据寄存器dst，有效元素在dst上连续排列，dst中后续非有效元素置0。若AR寄存器（用于累加已搬出的有效数据量）中累加了前序asc_squeeze_and_storeunalign指令的有效元素总数据量，则将dst中有效数据写入dst_addr + AR寄存器数据量的地址，并将本次执行的有效数据量大小（以字节为单位）累加进AR寄存器。如调用示例所示，多次连续调用本接口时，若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。。废弃卡明确指定 asc_squeeze_and_storeunalign 为迁移目标，目标卡给出筛选、连续非对齐搬出和 AR 自动偏移的替代合同，因此该边直接推进旧调用迁移。
- [asc_storeunalign_postupdate](asc_storeunalign_postupdate_deprecated.md)（`related`）：焦点卡给出明确迁移指令“该接口已废弃。请使用asc_squeeze_and_storeunalign实现此功能。”，候选替代接口说明“多次连续调用本接口时，若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。”；后者承接旧 postupdate 的连续非对齐搬出与地址更新职责。
- [AscSqueezeWithStatus](../compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的场景。。废弃接口卡明确把 asc_squeeze_and_storeunalign 指定为替代项，替代卡给出筛选有效元素并连续非对齐搬出到 UB 的完整契约，二者指向同一能力的旧新接口主题。
<!-- cannbot:related:end -->
