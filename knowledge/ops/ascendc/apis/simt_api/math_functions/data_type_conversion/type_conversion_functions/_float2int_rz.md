---
type: API
title: __float2int_rz
description: 遵循CAST_TRUNC模式，将浮点数转换为有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2int_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2int_rz

功能：遵循CAST_TRUNC模式，将浮点数转换为有符号整数，返回转换后的值。

函数原型：int __float2int_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的有符号整数。特殊值：±0→0；nan→0；inf→2147483647；-inf→-2147483648；超过INT_MAX范围的正值→2147483647；低于INT_MIN范围的负值→-2147483648。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/cast.md)（`related`）：__float2int_rz 与《Cast》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [Cast](../../../../simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`related`）：__float2int_rz 与《Cast》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [Truncate](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`related`）：__float2int_rz 与《Truncate》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [类型转换函数](type_conversion_functions.md)（`related`）：__float2int_rz 与《类型转换函数》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [AscFloat2int32](../../../../simd_api/c_api/vector_compute/asc_float2int32.md)（`same_topic`）：__float2int_rz 与《AscFloat2int32》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [__float2int_rd](_float2int_rd.md)（`same_topic`）：__float2int_rz 与《__float2int_rd》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [__float2int_rn](_float2int_rn.md)（`same_topic`）：__float2int_rz 与《__float2int_rn》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [__float2int_rna](_float2int_rna.md)（`same_topic`）：__float2int_rz 与《__float2int_rna》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [__float2int_ru](_float2int_ru.md)（`same_topic`）：__float2int_rz 与《__float2int_ru》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
<!-- cannbot:related:end -->
