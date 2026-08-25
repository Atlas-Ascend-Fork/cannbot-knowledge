---
type: API
title: __float_as_uint
description: 将浮点数中的位重新解释为无符号整数，即将浮点数存储的位按照无符号整数的格式进行读取。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float_as_uint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float_as_uint

功能：将浮点数中的位重新解释为无符号整数，即将浮点数存储的位按照无符号整数的格式进行读取。

函数原型：unsigned int __float_as_uint(const float x)

参数：x（输入）源操作数。

返回值：与输入浮点数最接近的整数值。特殊值：0→0；-0→2147483648；nan→2143289344；inf→ASCRT_INF_U；-inf→4286578688。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [类型转换函数](type_conversion_functions.md)（`related`）：bit reinterpret 与数值转换不同；总览用于区分两类入口。
- [__float_as_int](_float_as_int.md)（`same_topic`）：焦点处理float 位模式重解释为 uint32 及反向重解释；__float_as_int正文说明“将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取”。候选保持位级重解释而非数值转换，覆盖有符号视图和反向恢复。
- [__int_as_float](_int_as_float.md)（`same_topic`）：__int_as_float：__int_as_float 是逐位重解释而非数值转换；__float_as_int/__float_as_uint提供可逆方向，__uint_as_float覆盖无符号位模式。 目标卡《__float_as_uint》补充：将浮点数中的位重新解释为无符号整数，即将浮点数存储的位按照无符号整数的格式进行读取。
- [__uint_as_float](_uint_as_float.md)（`same_topic`）：焦点处理float 位模式重解释为 uint32 及反向重解释；__uint_as_float正文说明“将无符号整数中的位重新解释为浮点数，即将无符号整数存储的位按照float的格式进行读取”。候选保持位级重解释而非数值转换，覆盖有符号视图和反向恢复。
<!-- cannbot:related:end -->
