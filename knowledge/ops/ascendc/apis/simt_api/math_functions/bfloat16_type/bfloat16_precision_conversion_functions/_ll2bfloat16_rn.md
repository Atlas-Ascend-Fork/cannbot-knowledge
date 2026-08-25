---
type: API
title: __ll2bfloat16_rn
description: 遵循CAST_RINT模式，将int64类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__ll2bfloat16_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2bfloat16_rn

功能：遵循CAST_RINT模式，将int64类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __ll2bfloat16_rn(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的bfloat16类型数据。特殊值：0→0；9223372036854775807（INT64_MAX）→9.22337e+18；-9223372036854775808（INT64_MIN）→-9.22337e+18；257→256；32769→32768。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ll2bfloat16_rd](_ll2bfloat16_rd.md)（`same_topic`）：__ll2bfloat16_rd 与《__ll2bfloat16_rn》的实质衔接是：四种 ll→bfloat16 舍入接口仅舍入方向不同，必须结合输入边界和期望方向选择。
- [__ll2bfloat16_rna](_ll2bfloat16_rna.md)（`same_topic`）：两者都把 int64 转为 bfloat16，差别仅为 CAST_ROUND 与 CAST_RINT 舍入规则。
- [__ll2bfloat16_ru](_ll2bfloat16_ru.md)（`same_topic`）：__ll2bfloat16_ru 与《__ll2bfloat16_rn》的实质衔接是：ll→bfloat16 的 RU/RD/RN/RNA/RZ 只在舍入方向不同，边界输入必须据期望语义选型。
- [__ll2bfloat16_rz](_ll2bfloat16_rz.md)（`same_topic`）：RN 与 RZ 提供同一转换的最近偶数和向零模式。
<!-- cannbot:related:end -->
