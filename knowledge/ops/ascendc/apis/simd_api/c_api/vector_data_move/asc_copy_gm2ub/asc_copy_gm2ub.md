---
type: API
title: AscCopyGm2Ub
description: GM到UB数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub/asc_copy_gm2ub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscCopyGm2Ub

Global Memory到Unified Buffer数据搬运接口集合，用于将矢量计算的输入数据从GM搬运到UB。按硬件架构版本区分不同实现：asc_copy_gm2ub_arch_2201适用于Atlas A2训练/推理系列和Atlas A3训练/推理系列产品，asc_copy_gm2ub_arch_3510适用于Ascend 950PR/Ascend 950DT。开发者应根据目标硬件选择对应架构版本的接口，不同架构版本在数据块大小和地址对齐约束上可能存在差异。

<!-- cannbot:related:start -->
## 相关

- [Memory矢量计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/memory_vector_computation.md)（`explains`）：Memory矢量计算编程 与《AscCopyGm2Ub》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [AscCopyGm2UbAlign](../asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`related`）：普通版本和 Align 版本的地址/长度契约不同，应据物理对齐与尾块需求选择。
- [AscCopyUb2Gm](../asc_copy_ub2gm/asc_copy_ub2gm.md)（`related`）：反向 GM→UB 与本接口组成 copy-in/copy-out。
- [AscCopyUb2l1](../asc_copy_ub2l1.md)（`related`）：GM→UB 与 UB→L1 组成 GM→UB→L1 数据链。
- [AscNdimCopyGm2ub](../asc_ndim_copy_gm2ub.md)（`related`）：N 维非连续搬运应使用 AscNdimCopyGm2Ub，而线性/规则块用 AscCopyGm2Ub。
- [AscSetGm2ubLoop1Stride](../asc_set_gm2ub_loop1_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2Ub》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](../asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`same_topic`）：AscCopyGm2UbAlign 与《AscCopyGm2Ub》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [asc_copy_gm2ub](asc_copy_gm2ub_arch_2201.md)（`same_topic`）：asc_copy_gm2ub 与《AscCopyGm2Ub》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
- [asc_copy_gm2ub](asc_copy_gm2ub_arch_3510.md)（`same_topic`）：3510 变体给出 Ascend950 的签名和能力，用于避免套用 2201 约束。
<!-- cannbot:related:end -->
