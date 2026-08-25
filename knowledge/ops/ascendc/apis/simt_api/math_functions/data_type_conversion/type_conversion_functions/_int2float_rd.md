---
type: API
title: __int2float_rd
description: 遵循CAST_FLOOR模式，将int32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__int2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2float_rd

功能：遵循CAST_FLOOR模式，将int32类型数据转换为浮点数，返回转换后的值。

函数原型：float __int2float_rd(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：16777217（2^24+1）→ASCRT_TWO_TO_24_F；-16777217（-(2^24+1)）→-16777218；INT32_MAX→2147483520；INT32_MIN→-ASCRT_TWO_TO_31_F；INT32_MAX-1→2147483520；INT32_MIN+1→-ASCRT_TWO_TO_31_F。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2float_rn](_int2float_rn.md)（`same_topic`）：rn 提供最近舍入，可与 floor 模式在不可精确表示整数上做精度选型。
- [__int2float_rna](_int2float_rna.md)（`same_topic`）：rna 对 tie 采用远离零，是同一 int32→float 核心契约的另一舍入切面。
- [__int2float_ru](_int2float_ru.md)（`same_topic`）：ru 是同一转换的向上取整变体，与 rd 构成结果上下界。
- [__int2float_rz](_int2float_rz.md)（`same_topic`）：__int2float_rd说明遵循CAST_FLOOR模式，将int32类型数据转换为浮点数，返回转换后的值。
- [__uint2float_rd](_uint2float_rd.md)（`same_topic`）：__uint2float_rd 与《__int2float_rd》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
<!-- cannbot:related:end -->
