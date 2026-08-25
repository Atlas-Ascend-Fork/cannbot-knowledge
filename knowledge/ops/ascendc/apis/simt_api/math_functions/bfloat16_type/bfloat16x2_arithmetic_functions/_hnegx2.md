---
type: API
title: __hnegx2
description: 获取输入bfloat16x2_t类型数据各分量的负值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hnegx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnegx2

功能：获取输入bfloat16x2_t类型数据各分量的负值。

函数原型：bfloat16x2_t __hnegx2(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各分量的负值。特殊值：0→-0；-0→0；nan→nan；inf→-inf；-inf→inf；ASCRT_MAX_NORMAL_BF16→-ASCRT_MAX_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hneg](../bfloat16_arithmetic_functions/_hneg.md)（`same_topic`）：__hneg 与 __hnegx2 都对 bfloat16 数据逐分量取负，x2 版本只是把同一操作打包到两个 lane。
- [__hnegx2](../../half_type/half2_arithmetic_functions/_hnegx2.md)（`same_topic`）：《__hnegx2》处理“获取输入half2类型数据各分量的负值。”。《__hnegx2》明确提供“获取输入bfloat16x2_t类型数据各分量的负值。”，其参数、调用或验证步骤直接接入half2 逐 lane 取负与 bfloat16x2/scalar half 对应实现。
<!-- cannbot:related:end -->
