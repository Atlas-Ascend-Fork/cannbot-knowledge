---
type: API
title: __uint2bfloat16_rn
description: 遵循CAST_RINT模式，将uint32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__uint2bfloat16_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2bfloat16_rn

功能：遵循CAST_RINT模式，将uint32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __uint2bfloat16_rn(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的bfloat16类型数据。特殊值：0→0；257→256；514→512；1028→1024；4294967295（UINT32_MAX）→4.29497e+09。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2bfloat16_rna](_uint2bfloat16_rna.md)（`related`）：“特殊值：0→0；257→256；514→512”给出焦点端事实；“特殊值：0→0；257→258；4294967295（UINT32_MAX）→4294967296。”给出候选端事实。两端用同一输入 257 给出不同结果，直接呈现 RINT 与 ROUND 的舍入选择差异，能够用于转换接口选型和边界值验证。
<!-- cannbot:related:end -->
