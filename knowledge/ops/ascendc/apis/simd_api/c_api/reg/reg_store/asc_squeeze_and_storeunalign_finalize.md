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

- [AscSqueezeAndStoreunalign](asc_squeeze_and_storeunalign.md)（`related`）：约束：该接口中的dst_addr不需要32B对齐。；调用本接口后，需要调用asc_squeeze_and_storeunalign_finalize接口进行收尾。；首次调用本接口前或不想基于AR寄存器偏移时，需要调用asc_squeeze_and_storeunalign_init接口清空AR寄存器中的数据。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。 搬运原理如下： 记目的操作数的起始地址为dst_start，结束地址为dst_end，尾块元素个数为unalign_count = (dst_end - dst_end / 32 32) / sizeof(T)。则搬运的数据会分为两部分，分别是：。主接口的调用约束明确要求随后执行 finalize，目标接口专门把非对齐寄存器中剩余尾块搬到 UB，因此二者形成连续非对齐筛选存储的主体与收尾调用链。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：Init 卡说明“AR寄存器用于配合asc_squeeze_and_storeunalign及asc_squeeze_and_storeunalign_finalize使用”；Finalize 卡覆盖“从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。”。二者是同一 AR 驱动搬出序列的起始和收尾。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`same_topic`）：该接口已废弃。请使用asc_squeeze_and_storeunalign_finalize实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的尾块场景。 需要先调用下列接口之一后，再调用本接口。；reg计算数据搬运接口，适用于从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。 搬运原理如下： 记目的操作数的起始地址为dst_start，结束地址为dst_end，尾块元素个数为unalign_count = (dst_end - dst_end / 32 32) / sizeof(T)。则搬运的数据会分为两部分，分别是：。废弃卡明确指定 AscSqueezeAndStoreunalignFinalize 替代相同非对齐 UB 尾块收尾功能，目标卡给出新接口合同。
<!-- cannbot:related:end -->
