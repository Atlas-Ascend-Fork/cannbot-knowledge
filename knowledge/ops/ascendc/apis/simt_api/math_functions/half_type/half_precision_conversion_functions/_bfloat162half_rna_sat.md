---
type: API
title: __bfloat162half_rna_sat
description: 将bfloat16类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__bfloat162half_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162half_rna_sat

功能：将bfloat16类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。

函数原型：half __bfloat162half_rna_sat(const bfloat16_t x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_ROUND模式转换成的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162half_rna](_bfloat162half_rna.md)（`same_topic`）：遵循CAST_ROUND模式，将bfloat16类型数据转换为half类型数据；inf→ASCRT_MAX_NORMAL_FP16。两接口都是 bfloat16 到 half 的 CAST_ROUND 转换，`_sat` 变体明确把无穷钳到 FP16 最大正规值，提供是否采用饱和特殊值语义的直接选择。
<!-- cannbot:related:end -->
