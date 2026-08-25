---
type: API
title: Compares
description: 逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Compares.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Compares

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"。

该接口用于逐元素比较源操作数中每个元素与一个标量的大小关系，根据模板参数指定的比较模式（LT/GT/GE/EQ/NE/LE）判断结果是否为真，若为真则输出MaskReg对应比特位置1，否则置0。

参数：T: 矢量源操作数数据类型。；mode: 比较模式。支持如下取值： • LT：小于 • GT：大于 • GE：大于或等于 • EQ：等于 • NE：不等于 • LE：小于或等于；U: 矢量源操作数的RegTensor类型，由编译器自动推导，用户不需要填写。；S: 标量操作数数据类型。；dst(输出): MaskReg类型，目的操作数。；srcReg(输入): 源操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：通过mask参数控制的未选中元素在目的操作数中被置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEqScalar](../../../c_api/reg/compare_and_select/asc_eq_scalar.md)（`related`）：C++ Reg CompareScalar 与 C API AscEqScalar 提供同一标量比较任务的两种语言接口，可用于签名映射。
- [AscLeScalar](../../../c_api/reg/compare_and_select/asc_le_scalar.md)（`related`）：C++ Reg Compares 提供相同 tensor-scalar 谓词族，可在 C/C++ 接口间对照模式枚举和 mask。
- [AscLtScalar](../../../c_api/reg/compare_and_select/asc_lt_scalar.md)（`related`）：“Compares”定义：逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。；“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。。实质衔接：Reg Compares 生成 MaskReg；Compare 区分 tensor-tensor，Select 消费该 mask，AscLtScalar 展示 C API 的具体标量谓词映射。
- [Select](select.md)（`related`）：“Compares”定义：逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。；“Select”定义：根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。。实质衔接：Reg Compares 生成 MaskReg；Compare 区分 tensor-tensor，Select 消费该 mask，AscLtScalar 展示 C API 的具体标量谓词映射。
- [AscGeScalar](../../../c_api/reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Compares正文界定“逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [Compare](compare.md)（`same_topic`）：Compares 把第二个 RegTensor 换成标量，仍按 EQ/GT/LT/GE/NE/LE 生成 MaskReg。
- [Compares](../../memory_vector_compute/compare_and_select/compares.md)（`same_topic`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《Compares》具体提供“逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
<!-- cannbot:related:end -->
