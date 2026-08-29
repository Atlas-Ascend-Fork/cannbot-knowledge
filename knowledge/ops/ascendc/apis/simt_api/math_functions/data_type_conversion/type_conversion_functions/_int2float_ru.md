---
type: API
title: __int2float_ru
description: 遵循CAST_CEIL模式，将int32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__int2float_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2float_ru

功能：遵循CAST_CEIL模式，将int32类型数据转换为浮点数，返回转换后的值。

函数原型：float __int2float_ru(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777218；-16777217（-(2^24+1)）→-ASCRT_TWO_TO_24_F；2147483647 (INT32_MAX)→ASCRT_TWO_TO_31_F；-2147483648 (INT32_MIN)→-ASCRT_TWO_TO_31_F。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2float_rz](_int2float_rz.md)（`same_topic`）：“功能：遵循CAST_TRUNC模式，将int32类型数据转换为浮点数，返回转换后的值。”与“功能：遵循CAST_CEIL模式，将int32类型数据转换为浮点数，返回转换后的值。”提供双方正文证据。两端处理相同的 int32 到 float 转换，唯一关键选择是 CAST_TRUNC 与 CAST_CEIL 的舍入方向；互读能避免把截断和向上取整混用。
<!-- cannbot:related:end -->
