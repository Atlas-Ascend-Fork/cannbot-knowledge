---
type: API
title: H2Trunc
description: 获取对输入数据各元素的浮点数截断后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Trunc

功能：获取对输入数据各元素的浮点数截断后的整数。

函数原型：half2 h2trunc(half2 x)

参数：x（输入）源操作数。

返回值：输入数据各元素的浮点数截断后的整数。本接口受全局饱和寄存器影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Floor](h2floor.md)（`related`）：H2Trunc 与《H2Floor》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [H2Rint](h2rint.md)（`related`）：H2Trunc 与《H2Rint》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [AscTrunc](../../../../simd_api/c_api/reg/data_type_convert/asc_trunc.md)（`same_topic`）：AscTrunc 与 H2Trunc 都按向零方向把浮点值截到整数值并保持浮点载体；前者处理 Reg 向量，后者处理 half2 两 lane。
- [H2Trunc](../../bfloat16_type/bfloat16x2_math_functions/h2trunc.md)（`same_topic`）：H2Trunc 与《H2Trunc》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Htrunc](../half_math_functions/htrunc.md)（`same_topic`）：H2Trunc 与《Htrunc》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Trunc](../../../../simd_api/adv_api/math_compute/trunc_interface/trunc.md)（`same_topic`）：H2Trunc 与《Trunc》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Truncate](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《H2Trunc》明确“获取对输入数据各元素的浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncate](../../../../simd_api/basic_api/reg_vector_compute/type_conversion/truncate.md)（`same_topic`）：H2Trunc 与《Truncate》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Truncf](../../float_math_functions/truncf.md)（`same_topic`）：H2Trunc 与《Truncf》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
<!-- cannbot:related:end -->
