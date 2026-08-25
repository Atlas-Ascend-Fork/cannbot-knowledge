---
type: API
title: CompareStoreToRegister
description: 逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compare_store_to_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CompareStoreToRegister

逐元素比较两个 tensor，将比较结果存储到寄存器中。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Compares](compares.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《CompareStoreToRegister》具体提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《CompareStoreToRegister》明确提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](select.md)（`related`）：《Select》明确“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”；它与《CompareStoreToRegister》的“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”在实际调用参数、数据流或结果校验上直接衔接。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《CompareStoreToRegister》提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [SetCmpMask](set_cmp_mask_isasi.md)（`related`）：CompareStoreToRegister 产生比较掩码并写入 CMPMASK，SetCmpMask 则从内存显式装载 CMPMASK；二者是 Select 前置掩码的两条来源路径。
- [Compare](compare.md)（`same_topic`）：《Compare》明确“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”；它与《CompareStoreToRegister》的“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
