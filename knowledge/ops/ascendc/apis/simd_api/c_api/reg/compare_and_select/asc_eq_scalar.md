---
type: API
title: AscEqScalar
description: 根据mask将源操作数src中元素逐个与标量value比较是否相等，比较结果写入dst对应比特位，成立为1，不成立为0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_eq_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscEqScalar

根据mask，对src中的元素逐个与标量value进行比较（等于），将比较结果写入dst。dst为vector_bool类型，每个元素的比较结果占1个bit，1表示条件成立（等于），0表示不成立。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：dst中未被mask筛选的位置被置为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEq](asc_eq.md)（`related`）：AscEq 是同一 Reg 比较族的向量-向量等值接口，AscEqScalar 则把第二操作数收缩为标量。
- [Compares](../../../basic_api/reg_vector_compute/compare_and_select/compares.md)（`related`）：C++ Reg CompareScalar 与 C API AscEqScalar 提供同一标量比较任务的两种语言接口，可用于签名映射。
- [比较与选择](../../../basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`related`）：CompareAndSelect 总览定位 Reg 比较、掩码和选择流水，说明 AscEqScalar 的输出如何进入后续 Select。
- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscEqScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
<!-- cannbot:related:end -->
