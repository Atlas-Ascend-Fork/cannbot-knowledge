---
type: API
title: AscReduceMinDatablock
description: 根据mask将每个DataBlock中的最小值依次保存在目的操作数的最低位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_min_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMinDatablock

根据mask将每个DataBlock(32B)中的最小值依次保存在dst中的最低位。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 在比较中，遵循min(-0, +0) = -0。
- 找到源操作数中每个DataBlock内的最小值，连续写入到目的操作数，目的操作数中的其它元素置0。
- 未被mask选中的元素被视为最大值（浮点数为+inf），如果一个DataBlock中所有元素都未被mask选中，+inf将被填充到目的操作数的指定位置。
- 仅输出最值，不输出index下标。

仅 Ascend 950PR/Ascend 950DT 支持。
