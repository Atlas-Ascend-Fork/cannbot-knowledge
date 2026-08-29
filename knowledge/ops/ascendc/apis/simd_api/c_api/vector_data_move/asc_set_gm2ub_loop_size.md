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

- [AscSetGm2ubLoop1Stride](asc_set_gm2ub_loop1_stride.md)（`related`）：将数据从Global Memory (GM)搬运到Unified Buffer (UB)时，通过调用该接口设置内层循环中相邻迭代数据块间的间隔。；将数据从Global Memory (GM)搬运到Unified Buffer (UB)时，通过调用该接口设置数据搬运流程中的循环次数。；loop1 stride 与 loop size 分别配置同一次 GM 到 UB 循环搬运的步距和迭代次数，并共享使用后复位循环次数为一的状态约束。
<!-- cannbot:related:end -->
