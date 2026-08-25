---
type: API
title: __float2uint_rz
description: 遵循CAST_TRUNC模式，将浮点数转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2uint_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2uint_rz

功能：遵循CAST_TRUNC模式，将浮点数转换为无符号整数，返回转换后的值。

函数原型：unsigned int __float2uint_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的无符号整数。特殊值：±0→0；nan→0；inf→4294967295；-inf→0；1.5→1；超出uint32_t范围的正值→4294967295；负数→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2uint_rd](_float2uint_rd.md)（`same_topic`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_rz》说明遵循CAST_TRUNC模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_rn](_float2uint_rn.md)（`same_topic`）：RN 与 RZ 同为 float 到 uint32 转换，分别采用最近偶数和向零截断。
- [__float2uint_rna](_float2uint_rna.md)（`same_topic`）：__float2uint_rna 与《__float2uint_rz》的实质衔接是：__float2uint_rna 与 RN/RD/RU/RZ 变体保持 float→uint32 目标不变而替换舍入规则；signed int 和反向 uint→float RNA 说明符号/方向边界，类型转换总览统一特殊值契约。
- [__float2uint_ru](_float2uint_ru.md)（`same_topic`）：《__float2uint_ru》说明遵循CAST_CEIL模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_rz》说明遵循CAST_TRUNC模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint转换的rd/rn/rna/ru/rz仅舍入合同不同，类型转换总览提供这些模式的统一选择边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
