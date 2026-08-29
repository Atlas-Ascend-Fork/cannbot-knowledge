---
type: API
title: __float22half2_rd
description: 将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float22half2_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22half2_rd

功能：将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __float22half2_rd(const float2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_FLOOR模式转换成的half2类型数据。本接口受全局饱和寄存器的影响，。特殊值：±0→±0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rd_sat](_float22half2_rd_sat.md)（`same_topic`）：函数原型：half2 __float22half2_rd(const float2 x)；函数原型：half2 __float22half2_rd_sat(const float2 x)。两端接受同一 float2 并按 CAST_FLOOR 转为 half2，目标是带 `_sat` 名称的对应变体，应在选择饱和转换入口时共同核对。
<!-- cannbot:related:end -->
