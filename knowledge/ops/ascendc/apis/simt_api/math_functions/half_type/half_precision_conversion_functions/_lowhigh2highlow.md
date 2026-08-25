---
type: API
title: __lowhigh2highlow
description: 将输入数据的高低16位进行交换并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__lowhigh2highlow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __lowhigh2highlow

功能：将输入数据的高低16位进行交换并返回。

函数原型：half2 __lowhigh2highlow(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的高低16位进行交换的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__lowhigh2highlow](../../bfloat16_type/bfloat16_precision_conversion_functions/_lowhigh2highlow.md)（`related`）：两接口都交换 packed 双元素的高低 16 位，分别处理 half2 与 bfloat16x2。
<!-- cannbot:related:end -->
