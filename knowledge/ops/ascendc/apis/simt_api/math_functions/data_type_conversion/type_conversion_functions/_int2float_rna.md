---
type: API
title: __int2float_rna
description: 遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__int2float_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2float_rna

功能：遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。

函数原型：float __int2float_rna(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的浮点数。特殊值：2147483647 (INT32_MAX)→ASCRT_TWO_TO_31_F；-2147483648 (INT32_MIN)→-ASCRT_TWO_TO_31_F；16777217（2^24+1）→16777218；-16777217（-(2^24+1)）→-16777218。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2float_rn](_int2float_rn.md)（`related`）：“__int2float_rna”定义：遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。；“__int2float_rn”定义：遵循CAST_RINT模式，将int32类型数据转换为浮点数，返回转换后的值。。实质衔接：四张卡保持 int32→float，仅改变 RINT/CEIL/TRUNC/FLOOR；与焦点 RNA 的差异直接决定不可精确表示整数的舍入方向。
- [__int2float_rd](_int2float_rd.md)（`same_topic`）：rna 对 tie 采用远离零，是同一 int32→float 核心契约的另一舍入切面。
- [__int2float_ru](_int2float_ru.md)（`same_topic`）：rna 在平局时远离零，是最近舍入的另一变体。
- [__int2float_rz](_int2float_rz.md)（`same_topic`）：__int2float_rna说明遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。
- [__ll2float_rna](_ll2float_rna.md)（`same_topic`）：__ll2float_rna：所选转换保持ll→float或RNA语义，只切换有符号性、源位宽和RD/RN/RU/RZ舍入，能直接核对大整数不可精确表示时的方向。 目标卡《__int2float_rna》补充：遵循CAST_ROUND模式，将int32类型数据转换为浮点数，返回转换后的值。
<!-- cannbot:related:end -->
