---
type: API
title: __bfloat162bfloat162
description: 将输入数据填充为bfloat16x2前后两个分量，返回转换后的bfloat16x2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162bfloat162

将输入数据填充为bfloat16x2前后两个分量，返回转换后的bfloat16x2类型数据。
函数原型：bfloat16x2_t __bfloat162bfloat162(const bfloat16_t x)
返回值：输入的数据填充为bfloat16x2的数据。特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat1622float2](_bfloat1622float2.md)（`related`）：__bfloat1622float2 将 bfloat16x2 的两 lane 展开为 float2，是广播构造 bfloat16x2 后的直接宽化消费路径。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`related`）：__float22bfloat162_rn 从两个 float 分量构造 bfloat16x2，而本接口从单个 bfloat16 广播构造，二者输出布局一致。
- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`related`）：__float2bfloat162_rn 与《__bfloat162bfloat162》的实质衔接是：单个 float 填充 bf16x2 的 RNE 转换与双 float、双标量打包、标量转换和反向解包共享分量顺序与舍入契约。
- [__floats2bfloat162_rn](_floats2bfloat162_rn.md)（`related`）：__floats2bfloat162_rn 由两个独立标量填充两 lane，可与本接口的单值双 lane 广播按数据来源选用。
- [__halves2bfloat162](_halves2bfloat162.md)（`related`）：focal 将两个不同标量分别放入两个 lane，而 __bfloat162bfloat162 把同一标量广播到两个 lane；这是构造 packed 值时的关键选择。
- [bfloat16类型](../bfloat16_type.md)（`related`）：bfloat16 类型总览定义 bfloat16x2 数据类型、头文件与可用算术/转换族，是该构造接口的类型上下文。
<!-- cannbot:related:end -->
