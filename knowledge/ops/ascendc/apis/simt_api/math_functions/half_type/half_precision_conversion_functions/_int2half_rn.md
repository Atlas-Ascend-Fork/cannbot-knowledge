---
type: API
title: __int2half_rn
description: 遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2half_rn

功能：遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __int2half_rn(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的half类型数据。特殊值：0→0；±2049→±2048；±2051→±2052；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2half_rn_sat](_int2half_rn_sat.md)（`same_topic`）：功能：将int32类型数据按照CAST_RINT模式转换为half类型数据，返回转换后的值。；功能：遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。。两端共享 int32 到 half 的 CAST_RINT 转换；sat 变体还披露 SIMT 场景无法设置 CTRL、饱和模式不生效，互读可核对所谓饱和入口的实际行为。
<!-- cannbot:related:end -->
