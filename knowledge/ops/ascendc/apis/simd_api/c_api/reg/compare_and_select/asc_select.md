---
type: API
title: AscSelect
description: 根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscSelect

根据mask从源操作数src0、src1中选择元素，得到目的操作数dst。选择的规则为：当mask的比特位为1时，从src0中选取对应位置的数；当mask的比特位为0时，从src1中选取对应位置的数。

参数：`dst`(输出): 目的操作数（掩码寄存器或矢量数据寄存器）。；`src0`(输入): 源操作数0（掩码寄存器或矢量数据寄存器）。；`src1`(输入): 源操作数1（掩码寄存器或矢量数据寄存器）。；`mask`(输入): 源操作数掩码（掩码寄存器）。指定选择src0或src1为有效数据。mask的比特位为1时，选取src0；mask的比特位为0时，选取src1。

支持数据类型：half。

约束：- 通过mask参数控制的未选中的元素保持源操作数的值而非清零。
- src0、src1和dst的数据类型需要保持一致。

仅 Ascend 950PR/Ascend 950DT 支持。
