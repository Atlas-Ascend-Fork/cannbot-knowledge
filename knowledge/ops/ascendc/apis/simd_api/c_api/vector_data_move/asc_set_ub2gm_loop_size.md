---
type: API
title: AscSetUb2gmLoopSize
description: UB到GM搬运时，设置内层循环和外层循环的次数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ub2gm_loop_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetUb2gmLoopSize

将数据从Unified Buffer (UB)搬运到Global Memory (GM)时，通过调用该接口设置内层循环和外层循环的次数。 以源操作数搬运场景为例，如下图所示。
函数原型：void asc_set_ub2gm_loop_size(uint32_t loop1_size, uint32_t loop2_size)
约束：每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
