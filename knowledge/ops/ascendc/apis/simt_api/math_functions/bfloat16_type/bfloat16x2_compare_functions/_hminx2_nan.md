---
type: API
title: __hminx2_nan
description: 获取两个bfloat16x2_t类型数据各分量的最小值。任一分量为nan时，对应分量的计算结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hminx2_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hminx2_nan

功能：获取两个bfloat16x2_t类型数据各分量的最小值。任一分量为nan时，对应分量的计算结果为nan。

函数原型：bfloat16x2_t __hminx2_nan(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最小值。比较的分量x和y特殊值满足。特殊值：0→-0；-0→-0；任一分量含nan→nan；inf→y；(有限值,inf)→x；inf→-inf；-inf→-inf；-inf→-inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hminx2_nan](../../half_type/half2_compare_functions/_hminx2_nan.md)（`related`）：bfloat16x2 的同名 __hminx2_nan 保留逐分量最小值和 NaN 传播语义，但输入输出类型与头文件不同，可防止按名称误用 half2 重载。
- [__hmin_nan](../bfloat16_compare_functions/_hmin_nan.md)（`same_topic`）：__hmin_nan 与《__hminx2_nan》的实质衔接是：hmin 与 hmin_nan 的核心差别是 NaN 选择，hmax_nan 及 half2 版本提供相反极值和 packed 特殊值对照。
- [__hminx2](_hminx2.md)（`same_topic`）：《__hminx2》明确“获取两个bfloat16x2_t类型数据各分量的最小值。”；它与《__hminx2_nan》的“获取两个bfloat16x2_t类型数据各分量的最小值。任一分量为nan时，对应分量的计算结果为nan。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
