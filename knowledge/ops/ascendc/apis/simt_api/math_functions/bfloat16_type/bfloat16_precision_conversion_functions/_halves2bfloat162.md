---
type: API
title: __halves2bfloat162
description: 将两个bfloat16_t输入数据分别填充为bfloat16x2_t的前后两个分量，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__halves2bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __halves2bfloat162

将输入的数据分别填充为bfloat16x2前后两个分量，返回填充后数据。
函数原型：bfloat16x2_t __halves2bfloat162(const bfloat16_t x, const bfloat16_t y)
返回值：输入的数据分别填充为bfloat16x2前后两个分量，返回填充后数据。特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162bfloat162](_bfloat162bfloat162.md)（`related`）：focal 将两个不同标量分别放入两个 lane，而 __bfloat162bfloat162 把同一标量广播到两个 lane；这是构造 packed 值时的关键选择。
- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`related`）：__float2bfloat162_rn 与《__halves2bfloat162》的实质衔接是：单个 float 填充 bf16x2 的 RNE 转换与双 float、双标量打包、标量转换和反向解包共享分量顺序与舍入契约。
- [__floats2bfloat162_rn](_floats2bfloat162_rn.md)（`related`）：两接口都构造 bfloat16x2 的前后分量；候选在打包前执行 float→bfloat16 RINT，focal 则要求输入已经是 bfloat16。
- [__highs2bfloat162](_highs2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__halves2bfloat162》明确“将两个bfloat16_t输入数据分别填充为bfloat16x2_t的前后两个分量，返回填充后的数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__lows2bfloat162](_lows2bfloat162.md)（`same_topic`）：__lows2bfloat162 与《__halves2bfloat162》的实质衔接是：lows/highs、单输入复制与双输入拼装共同定义 bfloat16x2 低高 lane 的提取和构造顺序。
<!-- cannbot:related:end -->
