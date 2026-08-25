---
type: API
title: AscLtScalar
description: 根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_lt_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLtScalar

根据mask，对src中的元素逐个与标量value进行比较（小于），将比较结果写入dst。dst为vector_bool类型，每个元素的比较结果占1个bit，1表示条件成立，0表示不成立。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：dst中未被mask筛选的位置被置为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGtScalar](asc_gt_scalar.md)（`related`）：AscLtScalar说明根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0；对AscGtScalar而言，AscGtScalar 的标量右操作数语义需与 AscGt 的双 Tensor、AscLtScalar 的反向比较以及 Compare 的通用模式区分。
- [AscLt](asc_lt.md)（`related`）：“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。；“AscLt”定义：逐元素比较两个源操作数是否小于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。实质衔接：Vector 版保持 src 与 scalar 的 LT 语义但输出布局不同；Reg asc_lt 则把第二操作数改为寄存器，帮助选择正确重载。
- [Compares](../../../basic_api/reg_vector_compute/compare_and_select/compares.md)（`related`）：“Compares”定义：逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。；“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。。实质衔接：Reg Compares 生成 MaskReg；Compare 区分 tensor-tensor，Select 消费该 mask，AscLtScalar 展示 C API 的具体标量谓词映射。
- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscLtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLtScalar](../../vector_compute/asc_lt_scalar.md)（`same_topic`）：“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。；“AscLtScalar”定义：执行矢量中每个位置和标量比较，如果值小于标量值则为1，否则为0，结果为每个bit位按小端序排布。。实质衔接：Vector 版保持 src 与 scalar 的 LT 语义但输出布局不同；Reg asc_lt 则把第二操作数改为寄存器，帮助选择正确重载。
<!-- cannbot:related:end -->
