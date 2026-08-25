---
type: API
title: __highs2bfloat162
description: 分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__highs2bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __highs2bfloat162

功能：分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。

函数原型：bfloat16x2_t __highs2bfloat162(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：提取两个bfloat162输入的高16位，并填充到bfloat162中的结果。特殊值：±0→±0；nan→nan；±inf→±inf；ASCRT_MAX_NORMAL_BF16→ASCRT_MAX_NORMAL_BF16；-ASCRT_MAX_NORMAL_BF16→-ASCRT_MAX_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__halves2bfloat162](_halves2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__halves2bfloat162》明确“将两个bfloat16_t输入数据分别填充为bfloat16x2_t的前后两个分量，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__high2bfloat16](_high2bfloat16.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__highs2bfloat162》提供“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__high2bfloat162](_high2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__high2bfloat162》明确“将bfloat16x2_t输入数据的高16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__highs2half2](../../half_type/half_precision_conversion_functions/_highs2half2.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__highs2half2》明确“分别提取两个half2输入的高16位，并填充到half2中，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__low2bfloat162](_low2bfloat162.md)（`same_topic`）：__low2bfloat162 与《__highs2bfloat162》的实质衔接是：low/high 与单输入复制、双输入拼装接口共同定义 bfloat16x2 的分量选择和装配顺序。
- [__lowhigh2highlow](_lowhigh2highlow.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__lowhigh2highlow》明确“将bfloat16x2_t输入数据的高低16位进行交换，返回交换后的bfloat16x2_t数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__lows2bfloat162](_lows2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__lows2bfloat162》明确“分别提取两个bfloat162输入的低16位，并填充到bfloat162中，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
<!-- cannbot:related:end -->
