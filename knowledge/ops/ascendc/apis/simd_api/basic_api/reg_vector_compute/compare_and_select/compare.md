---
type: API
title: Compare
description: 逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Compare.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Compare

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"。

逐元素比较两个RegTensor大小，根据模板参数指定的比较模式，将比较结果写入目的操作数MaskReg中对应比特位，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。

其中cmp由模板参数mode指定比较模式，取值为EQ/GT/LT/GE/NE/LE。

参数：T: 操作数数据类型。；mode: 比较模式。支持如下取值： • LT：小于 • GT：大于 • GE：大于或等于 • EQ：等于 • NE：不等于 • LE：小于或等于；U: 源操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dst(输出): MaskReg类型，目的操作数。；srcReg0、srcReg1(输入): 源操作数。 类型为RegTensor。 两个源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：srcReg0和srcReg1可以是同一个RegTensor。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：该 runbook 展示 Compare 结果跨异步 VF 未完成即被 Select 读取造成 RAW 错选。
- [AscEq](../../../c_api/reg/compare_and_select/asc_eq.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“Compare”明确逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscGe](../../../c_api/reg/compare_and_select/asc_ge.md)（`related`）：Reg 基础 API Compare 以比较模式选择 GE 等谓词，是 AscGe C API 在 C++ Reg 层的对应能力。
- [Compare](../../memory_vector_compute/compare_and_select/compare.md)（`related`）：Memory Compare 在 LocalTensor 上执行同一谓词族，可按数据位置在 Memory 与 Reg 路线间选型。
- [Select](select.md)（`related`）：Compare 产生的 MaskReg 可直接驱动 Reg Select，组成比较后选择链。
- [AscLe](../../../c_api/reg/compare_and_select/asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；Compare正文说明“逐元素比较两个RegTensor大小，根据比较模式将结果写入MaskReg对应比特位，支持EQ/GT/LT/GE/NE/LE模式”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [Compares](compares.md)（`same_topic`）：Compares 把第二个 RegTensor 换成标量，仍按 EQ/GT/LT/GE/NE/LE 生成 MaskReg。
<!-- cannbot:related:end -->
