---
type: API
title: AscGeScalar
description: 对源操作数执行逐元素比较，若src_i大于等于标量value则目的操作数对应结果位为1，否则为0，每个元素比较结果占一个bit。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_ge_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscGeScalar

ge（greater than or equal to），对源操作数执行逐元素比较。对于src_i >= value，若条件成立则目的操作数对应结果位为1，否则为0，每个元素的比较结果占一个bit。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask未筛选的元素在输出中置零。
- 浮点数据类型比较，涉及nan时比较结果为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscGeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGe](asc_ge.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscGe正文界定“逐元素比较两个源操作数是否大于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [AscGe](../../vector_compute/asc_ge.md)（`same_topic`）：《AscGeScalar》明确“对源操作数执行逐元素比较，若src_i大于等于标量value则目的操作数对应结果位为1，否则为0，每个元素比较结果占一个bit。”；它与《AscGe》的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscGeScalar](../../vector_compute/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscGeScalar正文界定“按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [AscSelect](asc_select.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscSelect正文界定“根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [Compares](../../../basic_api/memory_vector_compute/compare_and_select/compares.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Compares正文界定“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [Compares](../../../basic_api/reg_vector_compute/compare_and_select/compares.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Compares正文界定“逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [ComparesFlexibleScalar](../../../basic_api/memory_vector_compute/compare_and_select/compares_flexible_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；ComparesFlexibleScalar正文界定“提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [Select](../../../basic_api/reg_vector_compute/compare_and_select/select.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Select正文界定“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
<!-- cannbot:related:end -->
