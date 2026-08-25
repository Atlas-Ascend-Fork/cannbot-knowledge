---
type: API
title: AscGtScalar
description: 根据mask将源操作数src按元素与标量value比较，若src_i大于value则目的操作数对应结果位为1，否则为0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_gt_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscGtScalar

根据mask将源操作数src按元素与标量value进行比较，若，则目的操作数对应结果位为1，否则为0。每个元素的比较结果占一个比特。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask未筛选的元素在输出中置零。
- 浮点数据类型比较，涉及nan时比较结果为0。

仅 Ascend 950PR/Ascend 950DT 支持。
