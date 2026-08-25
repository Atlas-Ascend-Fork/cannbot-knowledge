---
type: API
title: H2Floor
description: 获取小于或等于输入数据各元素的最大整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Floor

功能：获取小于或等于输入数据各元素的最大整数值。

函数原型：half2 h2floor(half2 x)

参数：x（输入）源操作数。

返回值：小于或等于输入数据各元素的最大整数值。本接口受全局饱和寄存器影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Ceil](h2ceil.md)（`related`）：“H2Ceil”定义：获取大于或等于输入数据各元素的最小整数值。；“H2Floor”定义：获取小于或等于输入数据各元素的最大整数值。。实质衔接：bfloat16x2 版保持双分量向上取整；H2Floor 是同 half2 输入的向下取整边界，二者用于明确舍入方向。
- [H2Trunc](h2trunc.md)（`related`）：H2Trunc 与《H2Floor》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [AscFloor](../../../../simd_api/c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《H2Floor》提供“获取小于或等于输入数据各元素的最大整数值。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Floorf](../../float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《H2Floor》明确“获取小于或等于输入数据各元素的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [H2Floor](../../bfloat16_type/bfloat16x2_math_functions/h2floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《H2Floor》提供“获取小于或等于输入数据各元素的最大整数值。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [H2Rint](h2rint.md)（`same_topic`）：H2Rint 取最近偶数，H2Floor 向负无穷取整；二者直接覆盖不同方向的 half2 整数化需求。
- [Hfloor](../half_math_functions/hfloor.md)（`same_topic`）：《Hfloor》处理“获取小于或等于输入half数据的最大整数值。”。《H2Floor》明确“获取小于或等于输入数据各元素的最大整数值。”，可直接用于核对half floor 与 float/half2、Reg/C API、高阶接口的同一取整语义。
<!-- cannbot:related:end -->
