---
type: API
title: AscSetGm2l1LoopSize
description: 设置GM到L1搬运流程中的循环次数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_gm2l1_loop_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSetGm2l1LoopSize

将数据从Global Memory (GM)搬运到L1 Buffer时，通过调用该接口设置数据搬运流程中的循环次数。

以源操作数搬运场景为例，如下图所示。

参数：loop1_size(输入): 内层循环的循环次数，取值范围为[0,2^21]。；loop2_size(输入): 外层循环的循环次数，取值范围为[0,2^21]。

约束：每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。

仅 Ascend 950PR/Ascend 950DT 支持。
