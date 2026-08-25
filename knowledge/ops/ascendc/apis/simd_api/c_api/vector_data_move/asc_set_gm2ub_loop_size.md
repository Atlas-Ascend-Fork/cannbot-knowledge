---
type: API
title: AscSetGm2ubLoopSize
description: GM到UB搬运时，设置数据搬运流程中的循环次数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_gm2ub_loop_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetGm2ubLoopSize

将数据从Global Memory (GM)搬运到Unified Buffer (UB)时，通过调用该接口设置数据搬运流程中的循环次数。 以源操作数搬运场景为例，如下图所示。
函数原型：void asc_set_gm2ub_loop_size(uint64_t loop1_size, uint64_t loop2_size)
约束：每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`related`）：AscCopyGm2UbAlign 与《AscSetGm2ubLoopSize》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [AscSetGm2ubLoop2Stride](asc_set_gm2ub_loop2_stride.md)（`related`）：AscSetGm2ubLoopSize 提供 loop1/loop2 次数，和 Loop2Stride 的间隔共同决定外层实际覆盖范围。
- [asc_copy_gm2ub](asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`related`）：asc_copy_gm2ub 与《AscSetGm2ubLoopSize》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
- [AscSetGm2ubLoop1Stride](asc_set_gm2ub_loop1_stride.md)（`same_topic`）：《AscSetGm2ubLoop1Stride》明确“GM到UB搬运时，设置内层循环中相邻迭代数据块间的间隔。”；它与《AscSetGm2ubLoopSize》的“GM到UB搬运时，设置数据搬运流程中的循环次数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
