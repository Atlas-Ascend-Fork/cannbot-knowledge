---
type: API
title: fp8数据转换函数
description: 提供float2、half2与FP8类型（e4m3、e5m2、hifloat8）之间的数据转换函数列表。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/fp8_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# fp8数据转换函数

提供 float2、half2 与 FP8 类型之间的数据转换，支持 hifloat8（__float22hif82 系列）、e4m3（__e4m3x22float2）和 e5m2（__e5m2x22float2）三种 FP8 编码格式。转换函数提供 rna 和 rh 两种舍入模式，部分带 _sat 后缀的变体支持饱和处理。适用于低精度量化与混合精度计算场景。
