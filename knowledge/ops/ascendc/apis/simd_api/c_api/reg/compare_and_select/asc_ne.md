---
type: API
title: AscNe
description: 逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_ne.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscNe

ne（not equal），该接口用于逐元素比较两个源操作数大小，将比较结果（）写入目的操作数dst对应比特位，如果比较结果为真，则对应比特位为1，否则为0。

参数：dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：src0和src1可以是同一个矢量数据寄存器。
- 浮点数据类型比较，涉及nan时比较结果为1。
- 当源操作数为浮点数据类型时，+0与-0视为相等。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEq](asc_eq.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“AscNe”明确逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscNe](../../vector_compute/asc_ne.md)（`same_topic`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscNe》说明逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscNeScalar](asc_ne_scalar.md)（`same_topic`）：AscNe说明逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
<!-- cannbot:related:end -->
