---
type: API
title: AscCopyGm2UbAlign
description: 提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscCopyGm2UbAlign

提供数据非对齐搬运的功能，将数据从Global Memory (GM)搬运到Unified Buffer (UB)，并支持8位/16位/32位数据类型搬运。 本接口支持以下两种数据搬运方式： 若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐，支持以下两种填充方式：
约束：本接口在非AIV上调用直接返回。；各存储单元的空间大小和对齐要求请参考存储单元说明。；如果本指令与其他指令的目的地址存在重叠，需要插入同步指令（asc_sync_notify和asc_sync_wait），保证多个指令的串行化，防止出现异常数据。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_3510.md)（`related`）：GM2UBAlign 负责非对齐输入搬入并可补齐，UB2GMAlign 负责反向搬出且丢弃 dummy、不支持设置填充值；二者构成 3510 非对齐 I/O 链。
- [AscSetGm2ubLoop1Stride](../asc_set_gm2ub_loop1_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2UbAlign》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align.md)（`same_topic`）：3510 变体给出 Ascend950 上的签名和尾块能力。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align_arch_2201.md)（`same_topic`）：AscCopyGm2UbAlign 与《AscCopyGm2UbAlign》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《AscCopyGm2UbAlign》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [asc_copy_gm2ub](../asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`same_topic`）：asc_copy_gm2ub 与《AscCopyGm2UbAlign》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
<!-- cannbot:related:end -->
