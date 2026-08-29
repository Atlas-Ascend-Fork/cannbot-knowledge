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

- [__uint2float_rz](_uint2float_rz.md)（`same_topic`）：“功能：遵循CAST_FLOOR模式，将uint32类型数据转换为浮点数，返回转换后的值。”与“功能：遵循CAST_TRUNC模式，将uint32类型数据转换为浮点数，返回转换后的值。”是双方正文中的具体合同。两端都将 uint32 转换为浮点数，并分别声明 CAST_FLOOR 与 CAST_TRUNC，互读可核对舍入模式和可表示边界。
<!-- cannbot:related:end -->
