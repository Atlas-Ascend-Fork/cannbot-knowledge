---
type: API
title: Compares
description: 逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compares.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Compares

逐元素比较 tensor 与标量值大小，结果为真则对应比特位为 1。支持 EQ、NE、GT、GE、LT、LE 等比较模式。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane](../../../../../runbooks/precision/compute_lane_count_must_follow_promoted_fp32_width.md)（`exemplifies`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》具体提供“2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [CompareStoreToRegister](compare_store_to_register.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《CompareStoreToRegister》具体提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Compares》明确提供“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](select.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《Select》具体提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《SelectFlexibleScalar》具体提供“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [SetCmpMask](set_cmp_mask_isasi.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《SetCmpMask》具体提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [AscGeScalar](../../../c_api/reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Compares正文界定“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [Compares](../../reg_vector_compute/compare_and_select/compares.md)（`same_topic`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《Compares》具体提供“逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [ComparesFlexibleScalar](compares_flexible_scalar.md)（`same_topic`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《ComparesFlexibleScalar》具体提供“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
<!-- cannbot:related:end -->
