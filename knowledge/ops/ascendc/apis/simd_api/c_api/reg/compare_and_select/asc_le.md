---
type: API
title: AscLe
description: 逐元素比较两个源操作数是否小于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_le.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLe

le（less than or equal to），该接口用于逐元素比较两个源操作数大小，将比较结果（）写入目的操作数dst对应比特位，如果比较结果为真，则对应比特位为1，否则为0。

参数：dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：src0和src1可以是同一个矢量数据寄存器。
- 浮点数据类型比较，涉及nan时比较结果为0。
- 当源操作数为浮点数据类型时，+0与-0视为相等。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLe](../../vector_compute/asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscLe正文说明“按元素判断src0 <= src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [AscLeScalar](asc_le_scalar.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscLeScalar正文说明“根据mask将源操作数src中元素逐个与标量value比较是否小于等于，比较结果写入dst对应比特位，成立为1，不成立为0”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [AscLeScalar](../../vector_compute/asc_le_scalar.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscLeScalar正文说明“按元素判断src <= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [AscSelect](asc_select.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscSelect正文说明“根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [Compare](../../../basic_api/reg_vector_compute/compare_and_select/compare.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；Compare正文说明“逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [Select](../../../basic_api/reg_vector_compute/compare_and_select/select.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；Select正文说明“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
<!-- cannbot:related:end -->
