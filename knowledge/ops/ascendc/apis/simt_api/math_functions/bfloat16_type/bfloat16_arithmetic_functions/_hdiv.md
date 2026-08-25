---
type: API
title: __hdiv
description: 计算两个bfloat16类型数据相除的结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hdiv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hdiv

计算两个bfloat16类型数据相除的结果，并遵循CAST_RINT模式对结果进行舍入。
函数原型：bfloat16_t __hdiv(const bfloat16_t x, const bfloat16_t y)
返回值：输入数据相除的结果。本接口受全局饱和模式影响，特殊值如下：
约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hdiv](../../half_type/half_arithmetic_functions/_hdiv.md)（`related`）：两卡都提供标量低精度 __hdiv，但分别以 half 与 bfloat16 为输入输出；数据精度和头文件决定入口选择。
- [__hdivx2](../bfloat16x2_arithmetic_functions/_hdivx2.md)（`related`）：标量 bfloat16 __hdiv 与 packed __hdivx2 使用相同 CAST_RINT 和特殊值规则，分别适配单值与双 lane 计算。
- [__fdividef](../../float_math_functions/_fdividef.md)（`same_topic`）：__fdividef 与《__hdiv》的实质衔接是：__fdividef 与 Fdividef 是 float 快速除法入口，half/half2 对应接口用于在降精度时保持相除语义和 lane 形态。
<!-- cannbot:related:end -->
