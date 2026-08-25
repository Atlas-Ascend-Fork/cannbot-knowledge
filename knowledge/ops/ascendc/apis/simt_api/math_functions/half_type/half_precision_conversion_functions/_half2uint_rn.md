---
type: API
title: __half2uint_rn
description: 遵循CAST_RINT模式，将half类型数据转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2uint_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2uint_rn

功能：遵循CAST_RINT模式，将half类型数据转换为无符号整数，返回转换后的值。

函数原型：unsigned int __half2uint_rn(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式将half类型数据转换为unsigned int类型数据。特殊值：±0→0；nan→0；inf→4294967295（uint32_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→0；0.5→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2uint_rn](../../data_type_conversion/type_conversion_functions/_float2uint_rn.md)（`related`）：float 源版本精度范围不同。
- [__half2uint_rd](_half2uint_rd.md)（`same_topic`）：rn nearest-even 与 focal rd floor 处理相同 half→uint32，非整数尤其负值附近会产生不同结果。
- [__half2uint_rna](_half2uint_rna.md)（`same_topic`）：两接口都执行 half→uint32 最近值舍入；RNA 为 ties-away，RN 为 ties-to-even，适合对照半整数输入的边界结果。
- [__half2uint_ru](_half2uint_ru.md)（`same_topic`）：RU 给向上结果。
- [__half2uint_rz](_half2uint_rz.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_rn 补充“遵循CAST_RINT模式，将half类型数据转换为无符号整数，返回转换后的值”。
<!-- cannbot:related:end -->
