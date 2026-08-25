---
type: API
title: AscSetUb2gmLoop1Stride
description: UB到GM搬运时，设置内层循环中相邻迭代数据块间的间隔。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ub2gm_loop1_stride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetUb2gmLoop1Stride

将数据从Unified Buffer (UB)搬运到Global Memory (GM)时，通过调用该接口设置内层循环中源操作数在相邻迭代间的数据块间隔，以及目的操作数在相邻迭代间的数据块间隔。 以源操作数搬运场景为例，如下图所示。
函数原型：void asc_set_ub2gm_loop1_stride(uint64_t loop1_src_stride, uint64_t loop1_dst_stride)
约束：每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyUb2Gm](asc_copy_ub2gm/asc_copy_ub2gm.md)（`related`）：AscCopyUb2Gm is the transfer operation that consumes the loop1 stride configured by the focal setter.
- [AscSetUb2gmLoop2Stride](asc_set_ub2gm_loop2_stride.md)（`related`）：Loop2Stride configures the outer-loop pitch that complements the focal loop1 pitch for multidimensional UB-to-GM copies.
- [AscSetUb2gmLoopSize](asc_set_ub2gm_loop_size.md)（`related`）：AscSetUb2gmLoopSize 定义内外层次数，Loop1Stride 定义同一次 UB→GM 搬运的内层地址递进，二者共同构成循环参数合同。
- [AscCopyUb2GmAlign](asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《AscSetUb2gmLoop1Stride》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [asc_copy_ub2gm](asc_copy_ub2gm/asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《AscSetUb2gmLoop1Stride》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
<!-- cannbot:related:end -->
