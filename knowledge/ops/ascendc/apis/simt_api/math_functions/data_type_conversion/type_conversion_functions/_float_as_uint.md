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

- [__uint_as_float](_uint_as_float.md)（`same_topic`）：功能：将无符号整数中的位重新解释为浮点数，即将无符号整数存储的位按照float的格式进行读取。；功能：将浮点数中的位重新解释为无符号整数，即将浮点数存储的位按照无符号整数的格式进行读取。。两端对同一 32 位存储做方向相反的 uint/float 位重解释，不进行数值舍入；联合阅读可完成编码与还原。
<!-- cannbot:related:end -->
