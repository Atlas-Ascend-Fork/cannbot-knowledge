---
type: API
title: ComparesFlexibleScalar
description: 提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compares_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ComparesFlexibleScalar

Compares 的灵活标量位置变体，支持标量操作数位置灵活配置。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [AscLeScalar](../../../c_api/vector_compute/asc_le_scalar.md)（`related`）：AscLeScalar 与《ComparesFlexibleScalar》的实质衔接是：Reg 与 Vector C API 及 ComparesFlexibleScalar 都实现 vector≤scalar，区别在结果载体与编程层级。
- [AscEqScalar](../../../c_api/vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《ComparesFlexibleScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGeScalar](../../../c_api/reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；ComparesFlexibleScalar正文界定“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [AscNeScalar](../../../c_api/reg/compare_and_select/asc_ne_scalar.md)（`same_topic`）：ComparesFlexibleScalar说明提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
- [Compares](compares.md)（`same_topic`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《ComparesFlexibleScalar》具体提供“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`same_topic`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《ComparesFlexibleScalar》提供“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
<!-- cannbot:related:end -->
