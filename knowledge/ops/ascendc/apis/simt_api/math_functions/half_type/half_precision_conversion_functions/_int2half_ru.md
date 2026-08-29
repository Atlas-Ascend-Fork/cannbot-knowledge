---
type: API
title: __int2half_ru
description: 遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2half_ru

功能：遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __int2half_ru(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的half类型数据。特殊值：0→0；ASCRT_MAX_NORMAL_FP16→inf；-ASCRT_MAX_NORMAL_FP16→-inf；2049→2050；-2049→-2048。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2half_ru_sat](_int2half_ru_sat.md)（`same_topic`）：功能：遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。；功能：将int32类型数据转换为half类型数据，并遵循CAST_CEIL模式，返回转换后的值。。两端共享 int32 到 half 的 CAST_CEIL 转换核心合同，后者增加 sat 命名及其平台饱和模式边界，联合阅读可核对是否需要该变体。
<!-- cannbot:related:end -->
