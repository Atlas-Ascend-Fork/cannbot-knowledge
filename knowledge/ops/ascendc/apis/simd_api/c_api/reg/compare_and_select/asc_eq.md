---
type: API
title: AscEq
description: 逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_eq.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscEq

eq表示相等（equal to），该接口用于逐元素比较两个源操作数大小，将比较结果（）写入目的操作数dst对应比特位，如果比较结果为真，则对应比特位为1，否则为0。

本接口仅在AIV上生效，非AIV调用直接返回。

参数：dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：half。

约束：- 本接口仅在AIV上生效，非AIV调用直接返回。
- 本接口在Vector Function（__simd_vf__标记的函数）内调用，dst为掩码寄存器，src0、src1为矢量数据寄存器。
- mask为vector_bool类型掩码寄存器，需通过掩码设置接口预先赋值后再传入；未赋值的掩码寄存器内容不确定，会导致有效元素位置错误。
- src0与src1的dtype需要保持一致。
- mask比特位为0时，dst对应比特位写0。
- 浮点比较时，+0与-0视为相等。
- 浮点比较输入含nan时，dst对应比特位写0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEq](../../vector_compute/asc_eq.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“AscEq”明确比较src0与src1在对应索引位置的元素大小。若比较结果为真，则输出结果的对应比特位设为1，否则设为0。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscEqScalar](asc_eq_scalar.md)（`related`）：AscEq 是同一 Reg 比较族的向量-向量等值接口，AscEqScalar 则把第二操作数收缩为标量。
- [AscNe](asc_ne.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“AscNe”明确逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscSelect](asc_select.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“AscSelect”明确根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [Compare](../../../basic_api/reg_vector_compute/compare_and_select/compare.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“Compare”明确逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscEq》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
<!-- cannbot:related:end -->
