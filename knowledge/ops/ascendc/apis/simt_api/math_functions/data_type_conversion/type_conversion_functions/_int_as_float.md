---
type: API
title: __int_as_float
description: 将整数中的位重新解释为浮点数，即将整数存储的位按照float的格式进行读取。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__int_as_float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int_as_float

功能：将整数中的位重新解释为浮点数，即将整数存储的位按照float的格式进行读取。

函数原型：float __int_as_float(const int x)

参数：x（输入）源操作数。

返回值：输入整数中的位重新解释成的浮点数。特殊值：0x00000000→0；0x80000000→-0；0x7F800000→inf；0xFF800000→-inf；0x7FFFFFFF→nan；0x7F7FFFFF→ASCRT_MAX_NORMAL_F；0xFF7FFFFF→-ASCRT_MAX_NORMAL_F。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float_as_int](_float_as_int.md)（`same_topic`）：__int_as_float：__int_as_float 是逐位重解释而非数值转换；__float_as_int/__float_as_uint提供可逆方向，__uint_as_float覆盖无符号位模式。 目标卡《__float_as_int》补充：将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。
- [__float_as_uint](_float_as_uint.md)（`same_topic`）：__int_as_float：__int_as_float 是逐位重解释而非数值转换；__float_as_int/__float_as_uint提供可逆方向，__uint_as_float覆盖无符号位模式。 目标卡《__float_as_uint》补充：将浮点数中的位重新解释为无符号整数，即将浮点数存储的位按照无符号整数的格式进行读取。
- [__uint_as_float](_uint_as_float.md)（`same_topic`）：__int_as_float：__int_as_float 是逐位重解释而非数值转换；__float_as_int/__float_as_uint提供可逆方向，__uint_as_float覆盖无符号位模式。 目标卡《__uint_as_float》补充：将无符号整数中的位重新解释为浮点数，即将无符号整数存储的位按照float的格式进行读取。
<!-- cannbot:related:end -->
