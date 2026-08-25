---
type: API
title: SelectFlexibleScalar
description: 提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# SelectFlexibleScalar

Select 的灵活标量变体，根据 mask 从源 tensor 和标量值中选择元素。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《Select dst==src 别名破坏张量输入值》提供“AscendC Select 在 dst 与 src0 或 src1 同一 LocalTensor 时先写 dst 破坏 src 原值，导致按 mask 应保留的源值被改成中间临时值；通过在 Select 后插入 DataCopy 探针或检查 dst==src 别名定位。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [CompareStoreToRegister](compare_store_to_register.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《CompareStoreToRegister》提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [Compares](compares.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《SelectFlexibleScalar》具体提供“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《SelectFlexibleScalar》明确提供“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [SetCmpMask](set_cmp_mask_isasi.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《SetCmpMask》提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [Squeeze](../../reg_vector_compute/compare_and_select/squeeze.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《SelectFlexibleScalar》补充：提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
- [比较与选择概述](overview.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《比较与选择概述》提供“Compare、Compares称之为比较接口，用于逐元素比较Tensor或Scalar的大小，并根据比较结果生成掩码。Select、GatherMask称之为选择接口，用于根据掩码条件从源操作数中选取元素输出到目的操作数。推荐使用场景如下：”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [AscEqScalar](../../../c_api/vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《SelectFlexibleScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [ComparesFlexibleScalar](compares_flexible_scalar.md)（`same_topic`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《ComparesFlexibleScalar》提供“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [Select](select.md)（`same_topic`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《Select》提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [Select](../../reg_vector_compute/compare_and_select/select.md)（`same_topic`）：SelectFlexibleScalar说明提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
<!-- cannbot:related:end -->
