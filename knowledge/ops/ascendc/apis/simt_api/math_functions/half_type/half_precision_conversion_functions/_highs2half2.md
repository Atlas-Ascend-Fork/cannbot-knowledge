---
type: API
title: __highs2half2
description: 分别提取两个half2输入的高16位，并填充到half2中，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__highs2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __highs2half2

功能：分别提取两个half2输入的高16位，并填充到half2中，返回填充后的数据。

函数原型：half2 __highs2half2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：分别提取两个half2输入的高16位，并填充到half2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__highs2bfloat162](../../bfloat16_type/bfloat16_precision_conversion_functions/_highs2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__highs2half2》明确“分别提取两个half2输入的高16位，并填充到half2中，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__lows2half2](_lows2half2.md)（`same_topic`）：__highs2half2 与 __lows2half2 分别从两个 half2 输入提取高/低 16bit lane，是成对的 lane 组装合同。
<!-- cannbot:related:end -->
