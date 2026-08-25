---
type: API
title: H2Trunc
description: 获取对输入数据各元素的浮点数截断后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Trunc

功能：获取对输入数据各元素的浮点数截断后的整数。

函数原型：bfloat16x2_t h2trunc(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各元素的浮点数截断后的整数。本接口受全局饱和模式影响，。特殊值：0→0；-0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→ASCRT_MIN_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscTrunc](../../../../simd_api/c_api/reg/data_type_convert/asc_trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《H2Trunc》说明获取对输入数据各元素的浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [H2Rint](h2rint.md)（`related`）：H2Trunc 向零截断，与 nearest-even 在小数输入上不同；可据目标舍入契约直接选择。
- [H2Trunc](../../half_type/half2_math_functions/h2trunc.md)（`same_topic`）：H2Trunc 与《H2Trunc》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Truncate](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《H2Trunc》明确“获取对输入数据各元素的浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncf](../../float_math_functions/truncf.md)（`same_topic`）：Truncf 与《H2Trunc》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
<!-- cannbot:related:end -->
