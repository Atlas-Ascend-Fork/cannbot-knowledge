---
type: API
title: reg数据搬入
description: 寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/reg_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# reg数据搬入

寄存器侧数据搬入接口将数据从Unified Buffer加载到矢量数据寄存器。基础接口含asc_load和asc_copy，asc_loadunalign及其pre/postupdate变体处理非对齐加载。
asc_loadalign及其变体支持对齐加载及多种数据变换：brc（广播）、deintlv（解交织）、downsample/upsample（下/上采样）、unpack（解包）等，postupdate变体支持地址寄存器后更新。asc_gather/gather_datablock提供收集式加载。asc_loadalign v1-v6已废弃。

<!-- cannbot:related:start -->
## 相关

- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../../../../../runbooks/compilation/reg_load_and_store_use_distinct_dist_enums.md)（`exemplifies`）：LoadDist 错用 DIST_NORM_B32 导致编译失败 与《reg数据搬入》的实质衔接是：该编译失败来自把 StoreDist::DIST_NORM_B32 套到 Reg LoadAlign；Reg load/LoadAlign 与 Store 总览直接展示 LoadDist 和 StoreDist 是两套枚举及正常 fp32 布局的配对。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《reg数据搬入》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [AscCopy](asc_copy.md)（`related`）：AscCopy 与《reg数据搬入》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [AscGather](../../vector_compute/asc_gather.md)（`related`）：AscGather 与《reg数据搬入》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [AscLoadalignDeintlvPostupdate](asc_loadalign_deintlv_postupdate.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《reg数据搬入》具体提供“寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《reg数据搬入》明确提供“寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
<!-- cannbot:related:end -->
