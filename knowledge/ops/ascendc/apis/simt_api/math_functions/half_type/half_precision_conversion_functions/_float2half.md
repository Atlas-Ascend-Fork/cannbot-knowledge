---
type: API
title: __float2half
description: 遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half

功能：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。

函数原型：half __float2half(const float x)

参数：x（输入）源操作数。

返回值：将float类型数据按照CAST_RINT模式转换为half类型数据。特殊值：±0→±0；nan→±0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“yPtr［idx］=__float2half(result_f32)”是 FP16 route 写回前的实际转换；“功能：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。”给出缩精度合同。
<!-- cannbot:related:end -->
