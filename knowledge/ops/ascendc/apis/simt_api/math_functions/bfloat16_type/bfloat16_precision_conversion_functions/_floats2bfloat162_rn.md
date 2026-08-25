---
type: API
title: __floats2bfloat162_rn
description: 将输入数据x、y遵循CAST_RINT模式分别转换为bfloat16类型，并填充到bfloat16x2的前后两部分，返回转换后的bfloat16x2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__floats2bfloat162_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __floats2bfloat162_rn

将输入数据x、y遵循CAST_RINT模式分别转换为bfloat16类型，并填充到bfloat16x2的前后两部分，返回转换后的bfloat16x2类型数据。
函数原型：bfloat16x2_t __floats2bfloat162_rn(const float x, const float y)
返回值：将输入float类型数据遵循CAST_RINT模式分别转换为bfloat16类型并填充到bfloat16x2的前后两部分，返回转换后的数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162bfloat162](_bfloat162bfloat162.md)（`related`）：__floats2bfloat162_rn 由两个独立标量填充两 lane，可与本接口的单值双 lane 广播按数据来源选用。
- [__float22bfloat162_rn_sat](_float22bfloat162_rn_sat.md)（`related`）：《__float22bfloat162_rn_sat》明确“饱和模式下，将float2类型数据的两个分量遵循CAST_RINT模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。”；它与《__floats2bfloat162_rn》的“将输入数据x、y遵循CAST_RINT模式分别转换为bfloat16类型，并填充到bfloat16x2的前后两部分，返回转换后的bfloat16x2类型数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`related`）：__float2bfloat162_rn 与《__floats2bfloat162_rn》的实质衔接是：单个 float 填充 bf16x2 的 RNE 转换与双 float、双标量打包、标量转换和反向解包共享分量顺序与舍入契约。
- [__floats2half2_rn](../../half_type/half_precision_conversion_functions/_floats2half2_rn.md)（`related`）：两个标量按 RINT 打包的结构相同，但目标低精度类型从 half2 变为 bfloat16x2。
- [__halves2bfloat162](_halves2bfloat162.md)（`related`）：两接口都构造 bfloat16x2 的前后分量；候选在打包前执行 float→bfloat16 RINT，focal 则要求输入已经是 bfloat16。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`same_topic`）：《__float22bfloat162_rn》明确“将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。”；它与《__floats2bfloat162_rn》的“将输入数据x、y遵循CAST_RINT模式分别转换为bfloat16类型，并填充到bfloat16x2的前后两部分，返回转换后的bfloat16x2类型数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [__lows2bfloat162](_lows2bfloat162.md)（`same_topic`）：__lows2bfloat162 与《__floats2bfloat162_rn》的实质衔接是：lows/highs、单输入复制与双输入拼装共同定义 bfloat16x2 低高 lane 的提取和构造顺序。
<!-- cannbot:related:end -->
