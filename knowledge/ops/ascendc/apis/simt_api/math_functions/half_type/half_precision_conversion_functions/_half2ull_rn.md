---
type: API
title: __half2ull_rn
description: 遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ull_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ull_rn

功能：遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。

函数原型：unsigned long long int __half2ull_rn(const half x)

参数：x（输入）源操作数。

返回值：遵循CAST_RINT模式，将half类型数据转换为usigned long long类型数据。特殊值：±0→0；0.5→0；1.5→2；nan→0；inf→18446744073709551615（uint64_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2ull_rna](_half2ull_rna.md)（`same_topic`）：“功能：遵循CAST_ROUND模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。”与“功能：遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。”提供双方正文证据。二者都是 half 到 unsigned long long 的转换，分别使用 CAST_ROUND 和 CAST_RINT；互读能直接核对中点舍入选择。
<!-- cannbot:related:end -->
