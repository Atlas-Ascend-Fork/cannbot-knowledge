---
type: API
title: __high2float
description: 将输入数据的高16位转换为float类型并返回结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__high2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __high2float

功能：将输入数据的高16位转换为float类型并返回结果。

函数原型：float __high2float(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的高16位转换为float类型的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2float](../../bfloat16_type/bfloat16_precision_conversion_functions/_high2float.md)（`related`）：该接口执行相同的高 16 位→float 操作，但输入为 half2；用于在 bfloat16x2 与 half2 两种 packed 类型间迁移实现。
<!-- cannbot:related:end -->
