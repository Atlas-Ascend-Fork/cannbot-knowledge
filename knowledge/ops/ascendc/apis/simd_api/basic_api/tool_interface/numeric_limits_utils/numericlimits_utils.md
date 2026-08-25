---
type: API
title: NumericLimits
description: NumericLimits工具类接口索引页，包含Max、Min、Lowest、Infinity、NaN及DeNormMin等数值极值方法。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/numericlimits_utils.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# NumericLimits

NumericLimits是查询指定数据类型数值属性的工具类，头文件为basic_api/kernel_operator_limits_intf.h，通过模板参数T指定数据类型。
提供Max/Lowest/Min/Infinity/NegativeInfinity/QuietNaN/SignalingNaN/DeNormMin八种极值查询，每种均有标量返回和为LocalTensor前count个元素赋值两种重载形式。
整数类型（int8_t/uint8_t/int16_t/uint16_t/int32_t/uint32_t）支持Max/Lowest/Min；浮点类型（half/bfloat16_t/float）额外支持Infinity/NegativeInfinity/QuietNaN/SignalingNaN/DeNormMin等浮点特有极值。
