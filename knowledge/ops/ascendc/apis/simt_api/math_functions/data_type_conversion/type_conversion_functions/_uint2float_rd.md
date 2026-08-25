---
type: API
title: __uint2float_rd
description: 遵循CAST_FLOOR模式，将uint32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__uint2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2float_rd

功能：遵循CAST_FLOOR模式，将uint32类型数据转换为浮点数，返回转换后的值。

函数原型：float __uint2float_rd(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：0→0；16777217 (2^24+1)→16777216；16777219 (2^24+3)→16777218；33554434 (2^25+2)→33554432；4294967295 (UINT32_MAX)→4294967040。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2float_rd](_int2float_rd.md)（`same_topic`）：__uint2float_rd 与《__int2float_rd》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__uint2float_rn](_uint2float_rn.md)（`same_topic`）：__uint2float_rd 与《__uint2float_rn》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__uint2float_rna](_uint2float_rna.md)（`same_topic`）：__uint2float_rd 与《__uint2float_rna》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__uint2float_ru](_uint2float_ru.md)（`same_topic`）：__uint2float_ru 与《__uint2float_rd》的实质衔接是：候选覆盖 uint32→float 的其他舍入方向、signed int 与 uint64 输入；它们直接对照 2^24+1 等不可精确表示整数在 ru 下的选择。
- [__uint2float_rz](_uint2float_rz.md)（`same_topic`）：__uint2float_rd 与《__uint2float_rz》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__ull2float_rd](_ull2float_rd.md)（`same_topic`）：__ull2float_rd 与《__uint2float_rd》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
<!-- cannbot:related:end -->
