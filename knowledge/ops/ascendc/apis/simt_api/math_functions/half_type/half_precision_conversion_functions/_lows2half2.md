---
type: API
title: __lows2half2
description: 分别提取两个half2输入的低16位，并填充到half2中，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__lows2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __lows2half2

功能：分别提取两个half2输入的低16位，并填充到half2中，返回填充后的数据。

函数原型：half2 __lows2half2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：分别提取两个half2输入的低16位，并填充到half2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→ASCRT_MIN_DENORM_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__halves2half2](_halves2half2.md)（`related`）：__halves2half2 从两个 half 标量构造 half2；lows/highs 版本则从两个 half2 抽分量，三者共同覆盖 half2 分量组装链。
- [__lows2bfloat162](../../bfloat16_type/bfloat16_precision_conversion_functions/_lows2bfloat162.md)（`related`）：__lows2bfloat162 与《__lows2half2》的实质衔接是：lows/highs、单输入复制与双输入拼装共同定义 bfloat16x2 低高 lane 的提取和构造顺序。
- [__highs2half2](_highs2half2.md)（`same_topic`）：__highs2half2 与 __lows2half2 分别从两个 half2 输入提取高/低 16bit lane，是成对的 lane 组装合同。
- [__low2half2](_low2half2.md)（`same_topic`）：__low2half2 与《__lows2half2》的实质衔接是：low2half 与 lows2half2 分别说明低 half 的标量提取、复制和双输入拼装语义。
<!-- cannbot:related:end -->
