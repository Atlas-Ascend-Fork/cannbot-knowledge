---
type: API
title: __hdivx2
description: 计算两个bfloat16x2_t类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hdivx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hdivx2

功能：计算两个bfloat16x2_t类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。

函数原型：bfloat16x2_t __hdivx2(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量相除的结果。相除的分量x和y满足。特殊值：(±0,±0,nan)→0；(±inf,±inf,nan)→0；(x，y任意一个为nan,nan)→0；(±inf,±0,±inf)→±ASCRT_MAX_NORMAL_BF16。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hdiv](../bfloat16_arithmetic_functions/_hdiv.md)（`related`）：标量 bfloat16 __hdiv 与 packed __hdivx2 使用相同 CAST_RINT 和特殊值规则，分别适配单值与双 lane 计算。
- [__hdivx2](../../half_type/half2_arithmetic_functions/_hdivx2.md)（`related`）：half2 版本 __hdivx2 与 focal 都做双分量并行除法和 CAST_RINT，差异在 half2 与 bfloat16x2 的精度、特殊值上界及头文件。
- [__fdividef](../../float_math_functions/_fdividef.md)（`same_topic`）：__fdividef 与《__hdivx2》的实质衔接是：__fdividef 与 Fdividef 是 float 快速除法入口，half/half2 对应接口用于在降精度时保持相除语义和 lane 形态。
- [bfloat16x2类型算术函数](bfloat16x2_arithmetic_functions.md)（`same_topic`）：bfloat16x2 算术函数汇总明确收录 __hdivx2，并把它与 packed 加减乘、FMA 和 ReLU 变体放在同一 API 族。
<!-- cannbot:related:end -->
