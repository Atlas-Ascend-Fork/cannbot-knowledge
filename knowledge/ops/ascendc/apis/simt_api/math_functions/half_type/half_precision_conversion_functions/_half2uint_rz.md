---
type: API
title: __half2uint_rz
description: 遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2uint_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2uint_rz

功能：遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值。

函数原型：unsigned int __half2uint_rz(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式，将half类型数据转换为unsigned int类型数据。特殊值：±0→0；nan→0；inf→4294967295（uint32_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2uint_rd](_half2uint_rd.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_rd 补充“遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值”。
- [__half2uint_rn](_half2uint_rn.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_rn 补充“遵循CAST_RINT模式，将half类型数据转换为无符号整数，返回转换后的值”。
- [__half2uint_rna](_half2uint_rna.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_rna 补充“遵循CAST_ROUND模式，将half类型数据转换为unsigned int类型数据，返回转换后的值”。
- [__half2uint_ru](_half2uint_ru.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_ru 补充“遵循CAST_CEIL模式，将half类型数据转换为unsigned int类型数据，返回转换后的值”。
<!-- cannbot:related:end -->
