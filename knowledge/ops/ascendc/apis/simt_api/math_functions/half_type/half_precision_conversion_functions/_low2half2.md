---
type: API
title: __low2half2
description: 将输入数据的低16位填充到half2并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__low2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __low2half2

功能：将输入数据的低16位填充到half2并返回。

函数原型：half2 __low2half2(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的低16位填充到half2的结果。特殊值：±0→±0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→ASCRT_MIN_DENORM_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__low2half](_low2half.md)（`same_topic`）：__low2half2 与《__low2half》的实质衔接是：low2half 与 lows2half2 分别说明低 half 的标量提取、复制和双输入拼装语义。
- [__lows2half2](_lows2half2.md)（`same_topic`）：__low2half2 与《__lows2half2》的实质衔接是：low2half 与 lows2half2 分别说明低 half 的标量提取、复制和双输入拼装语义。
<!-- cannbot:related:end -->
