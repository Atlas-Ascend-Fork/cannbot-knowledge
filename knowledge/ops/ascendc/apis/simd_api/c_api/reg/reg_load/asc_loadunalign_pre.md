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

- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：AscLoadunalignPre 与《连续非对齐场景优化》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadunalignPre》明确提供“用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadunalignPostupdate](asc_loadunalign_postupdate.md)（`related`）：AscLoadunalignPostupdate 正文明示需配合 asc_loadunalign_pre；Pre 初始化非对齐搬入状态，Postupdate 才能连续加载并更新源地址。
- [LoadUnAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_un_align_continuous.md)（`related`）：AscLoadunalignPre 与《LoadUnAlign》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscLoadunalignPre》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscLoadunalign](asc_loadunalign.md)（`same_topic`）：AscLoadunalignPre 与《AscLoadunalign》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [Load](../../../basic_api/reg_vector_compute/reg_data_load/load.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoadunalignPre》明确“用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
<!-- cannbot:related:end -->
