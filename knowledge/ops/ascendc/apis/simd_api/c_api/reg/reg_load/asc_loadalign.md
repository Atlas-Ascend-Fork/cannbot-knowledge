---
type: API
title: AscLoadalign
description: 从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalign

将Unified Buffer（UB）中起始地址32字节对齐的数据搬入矢量数据寄存器或掩码寄存器，搬运过程中数据格式和内容保持不变。本接口提供四种功能模式： 本接口仅在AIV上生效，非AIV调用直接返回。
约束：本接口仅在AIV上生效，非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；实际读取的UB地址和偏移后的UB地址必须32字节对齐，并且在UB地址空间内且不越界，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Reg LoadAlign 不接受 const __ubuf__ 指针](../../../../../runbooks/compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`exemplifies`）：该构建卡给出 LoadAlign 两参数 ABI 不接受 const __ubuf__ 指针的实测错误和完整调用链修复，是调用该接口时的直接编译诊断。
- [AscCopy](asc_copy.md)（`related`）：AscCopy 与《AscLoadalign》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadalign》明确提供“从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [AscLoadalignV1Deprecated](asc_loadalign_v1_deprecated.md)（`related`）：废弃 V1 的普通连续加载应迁移到现行 AscLoadalign，并由调用方继续显式维护源地址。
- [AscLoadalignV3Deprecated](asc_loadalign_v3_deprecated.md)（`related`）：AscLoadalignV3Deprecated 与《AscLoadalign》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
- [LoadAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_align_continuous.md)（`related`）：LoadAlign 是 AscLoadalign 连续模式的 C++ Reg 对应入口，两卡共同约束 32B 对齐 UB 地址、Vector Function 调用环境与寄存器装载。
- [LoadAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_align_mask_reg.md)（`related`）：AscLoadalign 的 C API 可把 32B 对齐 UB 搬入矢量寄存器或 MaskReg，并覆盖立即数、AddrReg 与非连续模式，是该基础 API 的 C 层映射。
- [LoadAlign](../../../basic_api/reg_vector_compute/reg_data_load/load_align_noncontinuous.md)（`related`）：LoadAlign 与《AscLoadalign》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [AscLoadalignUpsamplePostupdate](asc_loadalign_upsample_postupdate.md)（`same_topic`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscLoadalign》明确“从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [asc_loadalign (废弃)](asc_loadalign_v6_deprecated.md)（`same_topic`）：asc_loadalign (废弃) 与《AscLoadalign》的实质衔接是：AscLoadalign 是废弃 MaskReg 搬入重载的现行入口，承担同一 UB→Reg 对齐搬入任务。
<!-- cannbot:related:end -->
