---
type: API
title: __uint2float_rna
description: 遵循CAST_ROUND模式，将uint32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__uint2float_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2float_rna

功能：遵循CAST_ROUND模式，将uint32类型数据转换为浮点数，返回转换后的值。

函数原型：float __uint2float_rna(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的浮点数。特殊值：0→0；16777217 (2^24+1)→16777218；33554434 (2^25+2)→33554436；4294967295 (UINT32_MAX)→ASCRT_TWO_TO_32_F。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162uint_rna](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162uint_rna.md)（`related`）：反向 uint→float rna 用于检查转换链的数值往返，但不能替代 bfloat16→uint 的源精度约束。
- [__float2uint_rna](_float2uint_rna.md)（`related`）：__float2uint_rna 与《__uint2float_rna》的实质衔接是：__float2uint_rna 与 RN/RD/RU/RZ 变体保持 float→uint32 目标不变而替换舍入规则；signed int 和反向 uint→float RNA 说明符号/方向边界，类型转换总览统一特殊值契约。
- [__uint2float_rd](_uint2float_rd.md)（`same_topic`）：__uint2float_rd 与《__uint2float_rna》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__uint2float_rn](_uint2float_rn.md)（`same_topic`）：rn 与 rna 都做 uint→float 最近舍入，但 tie 处理不同；半值边界必须按参考契约选择。
- [__uint2float_ru](_uint2float_ru.md)（`same_topic`）：__uint2float_ru 与《__uint2float_rna》的实质衔接是：候选覆盖 uint32→float 的其他舍入方向、signed int 与 uint64 输入；它们直接对照 2^24+1 等不可精确表示整数在 ru 下的选择。
- [__uint2float_rz](_uint2float_rz.md)（`same_topic`）：rz 向零取整；对大整数不能精确表示时与 rna 可能产生不同 float。
<!-- cannbot:related:end -->
