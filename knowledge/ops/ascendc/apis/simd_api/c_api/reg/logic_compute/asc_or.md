---
type: API
title: AscOr
description: 根据mask对源操作数src0、src1执行按位或操作，结果写入dst，支持矢量数据寄存器和掩码寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_or.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscOr

根据mask对源操作数src0、src1执行按位或（|）操作，将结果写入目的操作数dst。

- 矢量数据寄存器按位或：对两个矢量数据寄存器执行按位或（|），结果写入目的矢量数据寄存器。

- 掩码寄存器按位或：对两个掩码寄存器执行按位或（|），结果写入目的掩码寄存器。

本接口仅在AIV上生效，非AIV调用直接返回。

参数：dst(输出): 目的操作数（矢量数据寄存器或掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器或掩码寄存器）。；src1(输入): 源操作数（矢量数据寄存器或掩码寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。 &bull;源操作数为矢量数据寄存器时，对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。 &bu。

支持数据类型：half。

约束：- 本接口仅在AIV上生效，非AIV调用直接返回。
- mask必须为vector_bool类型掩码寄存器，需通过掩码设置接口预先赋值后再传入；未赋值的掩码寄存器内容不确定，会导致有效元素位置错误。
- 参与计算的元素个数由矢量长度（VL）决定
    - 矢量数据寄存器按位或中元素个数 = VL ÷ sizeof(dtype)；
    - 掩码寄存器按位或中比特个数 = VL。
- src0、src1、dst的dtype需要保持一致。
- mask比特位为0时，dst对应比特位写0。

仅 Ascend 950PR/Ascend 950DT 支持。
