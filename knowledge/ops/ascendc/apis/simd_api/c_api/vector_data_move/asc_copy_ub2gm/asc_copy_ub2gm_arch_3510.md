---
type: API
title: asc_copy_ub2gm
description: 将数据从Unified Buffer (UB) 搬运到 Global Memory (GM)。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2gm/asc_copy_ub2gm_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_copy_ub2gm

将数据从Unified Buffer (UB) 搬运到 Global Memory (GM)。
函数原型：void asc_copy_ub2gm(__gm__ void* dst, __ubuf__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_ub2gm指令，且asc_copy_ub2gm指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_ub2gm指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetUb2gmLoop2Stride](../asc_set_ub2gm_loop2_stride.md)（`related`）：《asc_copy_ub2gm》明确“将数据从Unified Buffer (UB) 搬运到 Global Memory (GM)。”；它与《AscSetUb2gmLoop2Stride》的“UB到GM搬运时，设置外层循环中相邻迭代数据块间的间隔。”在实际调用参数、数据流或结果校验上直接衔接。
- [asc_copy_gm2ub](../asc_copy_gm2ub/asc_copy_gm2ub_arch_3510.md)（`related`）：3510 的 GM→UB 与 focal 的 UB→GM 构成 Vector tile 的搬入/搬出两端，且地址重叠时都要求插入同步避免异常数据。
- [AscCopyUb2Gm](asc_copy_ub2gm.md)（`same_topic`）：3510 变体给出 Ascend950 的签名和能力。
- [AscCopyUb2GmAlign](../asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《asc_copy_ub2gm》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [asc_copy_ub2gm](asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《asc_copy_ub2gm》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
<!-- cannbot:related:end -->
