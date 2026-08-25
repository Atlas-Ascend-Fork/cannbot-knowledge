---
type: API
title: AscLt
description: 逐元素比较两个源操作数是否小于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_lt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLt

lt（less than），该接口用于逐元素比较两个源操作数大小，将比较结果（）写入目的操作数dst对应比特位，如果比较结果为真，则对应比特位为1，否则为0。

参数：dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：src0和src1可以是同一个矢量数据寄存器。
- 浮点数据类型比较，涉及nan时比较结果为0。
- 当源操作数为浮点数据类型时，+0与-0视为相等。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLt](../../vector_compute/asc_lt.md)（`related`）：AscLt 与《AscLt》的实质衔接是：Reg 与 Vector AscLt 实现 vector-vector 小于比较，AscLtScalar 是标量右操作数的直接变体。
- [AscLtScalar](asc_lt_scalar.md)（`related`）：“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。；“AscLt”定义：逐元素比较两个源操作数是否小于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。实质衔接：Vector 版保持 src 与 scalar 的 LT 语义但输出布局不同；Reg asc_lt 则把第二操作数改为寄存器，帮助选择正确重载。
- [Compare](../../../basic_api/memory_vector_compute/compare_and_select/compare.md)（`related`）：Compare说明逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
- [Select](../../../basic_api/memory_vector_compute/compare_and_select/select.md)（`related`）：Select说明根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
<!-- cannbot:related:end -->
