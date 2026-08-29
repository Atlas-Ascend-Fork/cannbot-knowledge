---
type: API
title: AscSqueezeAndStoreunalignInit
description: 对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/system_variables_access/asc_squeeze_and_storeunalign_init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSqueezeAndStoreunalignInit

对AR特殊寄存器进行清零操作。AR寄存器用于配合asc_squeeze_and_storeunalign及asc_squeeze_and_storeunalign_finalize使用：当调用asc_squeeze_and_storeunalign后，有效元素的总字节数会被存入AR寄存器用于asc_squeeze_and_storeunalign接口内自动地址偏移。在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。
函数原型：void asc_squeeze_and_storeunalign_init()
约束：在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](../reg_store/asc_squeeze_and_storeunalign.md)（`related`）：Init 卡规定“在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。”；store API说明“若不清空AR寄存器，可以实现自动地址偏移，不需要手动管理地址。”。清零建立本轮连续搬出的偏移基点。
- [AscSqueezeAndStoreunalignFinalize](../reg_store/asc_squeeze_and_storeunalign_finalize.md)（`related`）：Init 卡说明“AR寄存器用于配合asc_squeeze_and_storeunalign及asc_squeeze_and_storeunalign_finalize使用”；Finalize 卡覆盖“从矢量数据寄存器中筛选出有效元素后按照连续非32B对齐的起始地址连续搬出到UB的尾块场景。”。二者是同一 AR 驱动搬出序列的起始和收尾。
- [asc_clear_ar_spr](asc_clear_ar_spr_deprecated.md)（`related`）：废弃接口明确“该接口已废弃。请使用asc_squeeze_and_storeunalign_init实现此功能。”；替代接口规定“在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。”。迁移目标和新调用顺序均由正文直接给出。
<!-- cannbot:related:end -->
