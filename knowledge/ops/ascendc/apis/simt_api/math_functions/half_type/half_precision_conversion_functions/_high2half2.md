---
type: API
title: __high2half2
description: 将输入数据的高16位填充到half2并返回结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__high2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __high2half2

功能：将输入数据的高16位填充到half2并返回结果。

函数原型：half2 __high2half2(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的的高16位填充到half2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__highs2half2](_highs2half2.md)（`same_topic`）：“功能：将输入数据的高16位填充到half2并返回结果。”与“功能：分别提取两个half2输入的高16位，并填充到half2中，返回填充后的数据。”是双方正文中的具体合同。两端都提取高 16 位构造 half2，单输入版本复制一个来源，高位双输入版本分别组合两个来源，互读可确认打包来源。
<!-- cannbot:related:end -->
