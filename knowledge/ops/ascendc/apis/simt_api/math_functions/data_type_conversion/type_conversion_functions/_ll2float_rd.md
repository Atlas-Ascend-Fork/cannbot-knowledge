---
type: API
title: __ll2float_rd
description: 遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ll2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2float_rd

功能：遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ll2float_rd(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：9223372036854775807（INT64_MAX）→9.223372e+18；-9223372036854775808（INT64_MIN）→-9.223372e+18；16777217（2^24+1 ）→ASCRT_TWO_TO_24_F；-16777217（-2^24-1）→-1.67772e+07；9007199254740993（2^53+1）→9.0072e+15；-9007199254740993（-2^53-1）→-9.0072e+15。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ll2float_rz](_ll2float_rz.md)（`same_topic`）：“功能：遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。”与“功能：遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。”是双方正文中的具体合同。两端都将 int64 转换为浮点数，分别采用向零截断与向下取整，互读能针对负数与非精确表示值选择舍入模式。
<!-- cannbot:related:end -->
