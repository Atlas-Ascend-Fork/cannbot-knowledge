---
type: API
title: AscCopyGm2UbAlign
description: 提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型，包含不同架构版本实现。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AscCopyGm2UbAlign

Global Memory到Unified Buffer对齐数据搬运接口集合，支持按指定对齐要求将数据从GM搬运到UB。相比asc_copy_gm2ub，本接口支持配置L2 Cache管理策略（通过asc_load_l2_cache_mode枚举指定），可优化重复数据访问场景的搬运效率。按硬件架构版本区分：asc_copy_gm2ub_align_arch_2201适用于Atlas A2/A3系列，asc_copy_gm2ub_align_arch_3510适用于Ascend 950PR/950DT。

<!-- cannbot:related:start -->
## 相关

- [Memory矢量计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/memory_vector_computation.md)（`explains`）：Memory矢量计算编程 与《AscCopyGm2UbAlign》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [AscCopyGm2Ub](../asc_copy_gm2ub/asc_copy_gm2ub.md)（`related`）：普通版本和 Align 版本的地址/长度契约不同，应据物理对齐与尾块需求选择。
- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align.md)（`related`）：反向对齐搬入与本接口组成 copy-in/copy-out。
- [AscLoadL2CacheMode](../../enum/asc_load_l2_cache_mode.md)（`related`）：AscCopyGm2UbAlign 直接接收 asc_load_l2_cache_mode，用它选择启用、驻留或 bypass L2 的 GM→UB 搬运策略。
- [AscNdimCopyGm2ub](../asc_ndim_copy_gm2ub.md)（`related`）：高维 stride 搬运应使用 Ndim 接口，不能用 Align 线性搬运伪装非连续布局。
- [AscSetCopyPadVal](../asc_set_copy_pad_val.md)（`related`）：AscSetCopyPadVal 负责“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；AscCopyGm2UbAlign 负责“提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型，包含不同架构版本实现”。
- [AscSetGm2ubLoop1Stride](../asc_set_gm2ub_loop1_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2UbAlign》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align_arch_2201.md)（`same_topic`）：AscCopyGm2UbAlign 与《AscCopyGm2UbAlign》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align_arch_3510.md)（`same_topic`）：3510 变体给出 Ascend950 上的签名和尾块能力。
- [asc_copy_gm2ub](../asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`same_topic`）：asc_copy_gm2ub 与《AscCopyGm2UbAlign》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
<!-- cannbot:related:end -->
