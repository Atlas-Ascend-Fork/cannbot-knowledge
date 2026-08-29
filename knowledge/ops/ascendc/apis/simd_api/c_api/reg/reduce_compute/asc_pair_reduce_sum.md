---
type: API
title: AscPairReduceSum
description: 将源操作数中每两个相邻数值相加，结果连续保存在目的操作数的低半部分。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_pair_reduce_sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscPairReduceSum

将传入的源操作数src中每两个相邻数值相加，并将相加的结果连续保存在目的操作数dst中的低半部分。以half数据类型为例，相加示意图

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算，不参与计算的元素相加时被当作0处理。

支持数据类型：float、half。

约束：- mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行累加。例如
  - 若连续两个元素a、b均不参与计算，目的操作数结果为0。
  - 若连续两个元素a、b仅元素a参与计算，目的操作数结果为a。
  - 若连续两个元素a、b仅元素b参与计算，目的操作数结果为b。

- 求和后，dst中仅前一半元素为有效数据，后一半填充为0。搬出至UB时需要避免数据踩踏。

仅 Ascend 950PR/Ascend 950DT 支持。
