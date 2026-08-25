---
type: API
title: AscLeScalar
description: 根据mask将源操作数src中元素逐个与标量value比较是否小于等于，比较结果写入dst对应比特位，成立为1，不成立为0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_le_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscLeScalar

根据mask，对src中的元素逐个与标量value进行比较（小于等于），将比较结果写入dst。dst为vector_bool类型，每个元素的比较结果占1个bit，1表示条件成立，0表示不成立。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：dst中未被mask筛选的位置被置为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLeScalar](../../vector_compute/asc_le_scalar.md)（`related`）：AscLeScalar 与《AscLeScalar》的实质衔接是：Reg 与 Vector C API 及 ComparesFlexibleScalar 都实现 vector≤scalar，区别在结果载体与编程层级。
- [Compares](../../../basic_api/reg_vector_compute/compare_and_select/compares.md)（`related`）：C++ Reg Compares 提供相同 tensor-scalar 谓词族，可在 C/C++ 接口间对照模式枚举和 mask。
- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscLeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLe](asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscLeScalar正文说明“根据mask将源操作数src中元素逐个与标量value比较是否小于等于，比较结果写入dst对应比特位，成立为1，不成立为0”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
<!-- cannbot:related:end -->
