---
type: API
title: __float_as_int
description: 将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float_as_int.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float_as_int

功能：将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。

函数原型：int __float_as_int(const float x)

参数：x（输入）源操作数。

返回值：输入的浮点数中的位重新解释成的有符号整数。特殊值：0→0；-0→ASCRT_MIN_VAL_S；nan→2143289344；inf→ASCRT_INT32_INF_S；-inf→-8388608；ASCRT_MAX_NORMAL_F→2139095039；-ASCRT_MAX_NORMAL_F→-8388609。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint_as_float](_uint_as_float.md)（`related`）：__uint_as_float说明将无符号整数中的位重新解释为浮点数，即将无符号整数存储的位按照float的格式进行读取；对__float_as_int而言，float 位模式可重解释为有符号或无符号整数；反向 int/uint-as-float 接口用于验证无数值转换的可逆位级契约。
- [__float_as_uint](_float_as_uint.md)（`same_topic`）：焦点处理float 位模式重解释为 uint32 及反向重解释；__float_as_int正文说明“将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取”。候选保持位级重解释而非数值转换，覆盖有符号视图和反向恢复。
- [__int_as_float](_int_as_float.md)（`same_topic`）：__int_as_float：__int_as_float 是逐位重解释而非数值转换；__float_as_int/__float_as_uint提供可逆方向，__uint_as_float覆盖无符号位模式。 目标卡《__float_as_int》补充：将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。
<!-- cannbot:related:end -->
