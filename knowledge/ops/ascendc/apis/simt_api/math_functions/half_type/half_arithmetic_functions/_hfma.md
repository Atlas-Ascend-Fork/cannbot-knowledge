---
type: API
title: __hfma
description: 对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hfma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __hfma

功能：对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hfma(half x, half y, half z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：x * y + z的值。本接口受全局饱和模式影响，。特殊值：(x*y = inf,-inf,nan)→0；(x*y = -inf,inf,nan)→0；(x*y+z超出ASCRT_MAX_NORMAL_FP16,inf)→ASCRT_MAX_NORMAL_FP16；(x*y+z小于ASCRT_MAX_NORMAL_FP16,-inf)→-ASCRT_MAX_NORMAL_FP16；(x、y、z任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hfma_relu](_hfma_relu.md)（`related`）：功能：对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。；功能：对输入half类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。。两接口共享 half FMA 与 CAST_RINT 核心计算，目标接口在同一结果后增加负数钳零，适合据是否需要融合 ReLU 选型。
<!-- cannbot:related:end -->
