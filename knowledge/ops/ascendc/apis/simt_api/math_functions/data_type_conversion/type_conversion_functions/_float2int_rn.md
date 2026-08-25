---
type: API
title: __float2int_rn
description: 遵循CAST_RINT模式，将浮点数转换为有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2int_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2int_rn

功能：遵循CAST_RINT模式，将浮点数转换为有符号整数，返回转换后的值。

函数原型：int __float2int_rn(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的有符号整数。特殊值：±0→0；nan→0；inf→2147483647；-inf→-2147483648；ASCRT_MAX_NORMAL_F→2147483647；-ASCRT_MAX_NORMAL_F→-2147483648；±0.5→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/cast.md)（`related`）：__float2int_rn 与《Cast》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [Cast](../../../../simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`related`）：__float2int_rn 与《Cast》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [类型转换函数](type_conversion_functions.md)（`related`）：__float2int_rn 与《类型转换函数》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [AscFloat2int32](../../../../simd_api/c_api/vector_compute/asc_float2int32.md)（`same_topic`）：__float2int_rn 与《AscFloat2int32》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rd](_float2int_rd.md)（`same_topic`）：__float2int_rn 与《__float2int_rd》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rna](_float2int_rna.md)（`same_topic`）：__float2int_rn 与《__float2int_rna》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_ru](_float2int_ru.md)（`same_topic`）：__float2int_rn 与《__float2int_ru》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rz](_float2int_rz.md)（`same_topic`）：__float2int_rz 与《__float2int_rn》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
<!-- cannbot:related:end -->
