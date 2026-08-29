---
type: API
title: AscDiv
description: 根据mask对源操作数src0、src1按元素求商，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscDiv

该接口根据mask，对源操作数src0、src1进行按元素求商操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 注意除零错误，结果

仅 Ascend 950PR/Ascend 950DT 支持。
