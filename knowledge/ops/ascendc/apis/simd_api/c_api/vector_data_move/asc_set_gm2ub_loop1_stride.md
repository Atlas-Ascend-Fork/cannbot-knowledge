---
type: API
title: AscSetGm2ubLoop1Stride
description: GM到UB搬运时，设置内层循环中相邻迭代数据块间的间隔。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_gm2ub_loop1_stride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetGm2ubLoop1Stride

将数据从Global Memory (GM)搬运到Unified Buffer (UB)时，通过调用该接口设置内层循环中相邻迭代数据块间的间隔。 以源操作数搬运场景为例，如下图所示。
函数原型：void asc_set_gm2ub_loop1_stride(uint64_t loop1_src_stride, uint64_t loop1_dst_stride)
约束：每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2Ub](asc_copy_gm2ub/asc_copy_gm2ub.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2Ub》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2UbAlign》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2UbAlign》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_3510.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscCopyGm2UbAlign》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscSetGm2ubLoop2Stride](asc_set_gm2ub_loop2_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《AscSetGm2ubLoop2Stride》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [asc_copy_gm2ub](asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`related`）：AscSetGm2ubLoop1Stride 与《asc_copy_gm2ub》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [asc_copy_gm2ub](asc_copy_gm2ub/asc_copy_gm2ub_arch_3510.md)（`related`）：AscSetGm2ubLoop1Stride 与《asc_copy_gm2ub》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [矢量数据搬运](vector_data_move.md)（`related`）：AscSetGm2ubLoop1Stride 与《矢量数据搬运》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [AscSetGm2ubLoopSize](asc_set_gm2ub_loop_size.md)（`same_topic`）：《AscSetGm2ubLoop1Stride》明确“GM到UB搬运时，设置内层循环中相邻迭代数据块间的间隔。”；它与《AscSetGm2ubLoopSize》的“GM到UB搬运时，设置数据搬运流程中的循环次数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
