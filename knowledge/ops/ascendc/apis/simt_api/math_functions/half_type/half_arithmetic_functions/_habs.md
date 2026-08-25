---
type: API
title: __habs
description: 获取输入数据的绝对值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__habs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __habs

功能：获取输入数据的绝对值。

函数原型：half __habs(half x)

参数：x（输入）源操作数。

返回值：输入数据的绝对值。本接口不受全局饱和模式影响，。特殊值：±0→0；inf→inf；-inf→inf；nan→nan。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hneg](_hneg.md)（`related`）：HNeg 改符号，HAbs 清除数值符号；负零/NaN 语义需分别验证。
- [half类型算术函数](half_arithmetic_functions.md)（`related`）：半精度算术总页给出 HAbs 的支持平台、NaN 和舍入约束，是函数使用语境。
- [__habs](../../bfloat16_type/bfloat16_arithmetic_functions/_habs.md)（`same_topic`）：half 与 bfloat16 标量 Abs 完成相同绝对值运算，源精度不同。
<!-- cannbot:related:end -->
