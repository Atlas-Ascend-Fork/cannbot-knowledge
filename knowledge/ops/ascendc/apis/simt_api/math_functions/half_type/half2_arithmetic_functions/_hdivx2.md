---
type: API
title: __hdivx2
description: 计算两个half2类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/__hdivx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hdivx2

功能：计算两个half2类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。

函数原型：half2 __hdivx2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量相除的结果。本接口受全局饱和寄存器的影响，。特殊值：(±0,±0,nan)→0；(±inf,±inf,nan)→0；(±inf,±0,±inf)→±ASCRT_MAX_NORMAL_FP16；(x或y为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hdivx2](../../bfloat16_type/bfloat16x2_arithmetic_functions/_hdivx2.md)（`related`）：half2 版本 __hdivx2 与 focal 都做双分量并行除法和 CAST_RINT，差异在 half2 与 bfloat16x2 的精度、特殊值上界及头文件。
<!-- cannbot:related:end -->
