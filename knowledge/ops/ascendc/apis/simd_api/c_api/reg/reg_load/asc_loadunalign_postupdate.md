---
type: API
title: AscLoadunalignPostupdate
description: 从UB非32B对齐地址连续搬入数据并自动更新源地址，配合asc_loadunalign_pre使用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadunalign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadunalignPostupdate

数据搬运接口，适用于从UB非32B对齐地址起始连续搬入。
函数原型：void asc_loadunalign_postupdate(vector_int8_t& dst, vector_load_unalign& src0, __ubuf__ int8_t*& src1, uint32_t count)
约束：接口中的src1不需要32B对齐。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadunalignPre](asc_loadunalign_pre.md)（`related`）：AscLoadunalignPostupdate 正文明示需配合 asc_loadunalign_pre；Pre 初始化非对齐搬入状态，Postupdate 才能连续加载并更新源地址。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscLoadunalignPostupdate》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscLoadunalign](asc_loadunalign.md)（`same_topic`）：普通版本要求用户手动推进 UB 地址，Postupdate 版本把地址更新合并进调用，是同一载入的循环组织选项。
<!-- cannbot:related:end -->
