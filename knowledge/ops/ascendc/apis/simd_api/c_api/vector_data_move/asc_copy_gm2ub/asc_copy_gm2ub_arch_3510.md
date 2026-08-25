---
type: API
title: asc_copy_gm2ub
description: 将数据从Global Memory (GM) 搬运到 Unified Buffer (UB)。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub/asc_copy_gm2ub_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_copy_gm2ub

将数据从Global Memory (GM) 搬运到 Unified Buffer (UB)。
函数原型：void asc_copy_gm2ub(__ubuf__ void* dst, __gm__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2ub指令，且asc_copy_gm2ub指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2ub指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetGm2ubLoop1Stride](../asc_set_gm2ub_loop1_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《asc_copy_gm2ub》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscSetGm2ubLoop2Stride](../asc_set_gm2ub_loop2_stride.md)（`related`）：Loop2Stride 配置的硬件循环状态由随后 asc_copy_gm2ub 搬运消费；目的地址重叠时还需显式同步。
- [asc_copy_ub2gm](../asc_copy_ub2gm/asc_copy_ub2gm_arch_3510.md)（`related`）：3510 的 GM→UB 与 focal 的 UB→GM 构成 Vector tile 的搬入/搬出两端，且地址重叠时都要求插入同步避免异常数据。
- [AscCopyGm2Ub](asc_copy_gm2ub.md)（`same_topic`）：3510 变体给出 Ascend950 的签名和能力，用于避免套用 2201 约束。
- [AscCopyGm2UbAlign](../asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`same_topic`）：AscCopyGm2UbAlign 与《asc_copy_gm2ub》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [asc_copy_gm2ub](asc_copy_gm2ub_arch_2201.md)（`same_topic`）：asc_copy_gm2ub 与《asc_copy_gm2ub》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
- [asc_copy_ub2gm](../asc_copy_ub2gm/asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《asc_copy_gm2ub》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
<!-- cannbot:related:end -->
