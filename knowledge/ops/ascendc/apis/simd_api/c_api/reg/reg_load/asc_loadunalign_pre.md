---
type: API
title: AscLoadunalignPre
description: 用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadunalign_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadunalignPre

用于在进行非对齐数据搬入前的初始化，需配合asc_loadunalign接口使用。
函数原型：void asc_loadunalign_pre(vector_load_unalign& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadunalign](asc_loadunalign.md)（`related`）：调用该接口之前，需要调用asc_loadunalign_pre进行非对齐搬入前的初始化。；用于在进行非对齐数据搬入前的初始化，需配合asc_loadunalign接口使用。。执行卡要求调用前置初始化，初始化卡又明确必须与执行接口配合，形成固定调用顺序。
- [AscLoadunalignPostupdate](asc_loadunalign_postupdate.md)（`related`）：“数据搬运接口，适用于从UB非32B对齐地址起始连续搬入。”明确给出左端事实；“用于在进行非对齐数据搬入前的初始化，需配合asc_loadunalign接口使用。”明确给出右端事实。Pre 初始化 vector_load_unalign 状态，Postupdate 以该状态从非 32B 对齐 UB 连续搬入并更新源指针，形成成对调用契约。
<!-- cannbot:related:end -->
