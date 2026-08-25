---
type: API
title: __hfma_relu
description: 对输入half类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hfma_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfma_relu

功能：对输入half类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。

函数原型：half __hfma_relu(const half x, const half y, const half z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：x * y + z的值，若结果为负数，置为0。本接口受全局饱和模式影响，。特殊值：(x*y = inf,-inf,nan)→0；(x*y = -inf,inf,nan)→0；(x*y+z超出ASCRT_MAX_NORMAL_FP16,inf)→ASCRT_MAX_NORMAL_FP16；(x*y+z小于ASCRT_MIN_NORMAL_FP16,0)→0；(x、y、z任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
