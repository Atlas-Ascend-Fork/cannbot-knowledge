---
type: API
title: __halves2half2
description: 将输入的数据分别填充为half2前后两个分量，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__halves2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __halves2half2

功能：将输入的数据分别填充为half2前后两个分量，返回填充后的数据。

函数原型：half2 __halves2half2(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入的数据分别填充为half2前后两个分量的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__floats2half2_rn](_floats2half2_rn.md)（`related`）：《__floats2half2_rn》明确“将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。”；它与《__halves2half2》的“将输入的数据分别填充为half2前后两个分量，返回填充后的数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [__lows2half2](_lows2half2.md)（`related`）：__halves2half2 从两个 half 标量构造 half2；lows/highs 版本则从两个 half2 抽分量，三者共同覆盖 half2 分量组装链。
<!-- cannbot:related:end -->
