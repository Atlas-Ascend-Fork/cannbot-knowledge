---
type: API
title: AscLoadunalign
description: 从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadunalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadunalign

reg计算数据搬运接口，适用于从UB非32B对齐的起始地址连续搬入矢量数据寄存器的场景。 该接口不改变源操作数在UB上的地址，每次循环的调用都需要用户手动更新源操作数在UB上的地址。
函数原型：void asc_loadunalign(vector_int8_t& dst, vector_load_unalign& src0, __ubuf__ int8_t *src1)
约束：该接口中的src1不需要32B对齐。；调用该接口之前，需要调用asc_loadunalign_pre进行非对齐搬入前的初始化。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadunalign》明确提供“从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscLoadunalign》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [AscLoadunalignPostupdate](asc_loadunalign_postupdate.md)（`same_topic`）：普通版本要求用户手动推进 UB 地址，Postupdate 版本把地址更新合并进调用，是同一载入的循环组织选项。
- [AscLoadunalignPre](asc_loadunalign_pre.md)（`same_topic`）：AscLoadunalignPre 与《AscLoadunalign》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [Load](../../../basic_api/reg_vector_compute/reg_data_load/load.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoadunalign》明确“从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [LoadUnAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_un_align_continuous.md)（`same_topic`）：两者都是连续非对齐 Reg 搬入，分别为 C++ RegTensor 与 C API 形式，且共享预处理状态的使用约束。
<!-- cannbot:related:end -->
