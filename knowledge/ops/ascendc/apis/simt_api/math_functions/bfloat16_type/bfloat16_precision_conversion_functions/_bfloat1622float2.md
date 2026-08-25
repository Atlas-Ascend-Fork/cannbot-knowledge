---
type: API
title: __bfloat1622float2
description: 将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat1622float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat1622float2

将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。
函数原型：float2 __bfloat1622float2(const bfloat16x2_t x)
返回值：将bfloat16x2的两个分量分别转换为float，并填充到float2的结果。特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162bfloat162](_bfloat162bfloat162.md)（`related`）：__bfloat1622float2 将 bfloat16x2 的两 lane 展开为 float2，是广播构造 bfloat16x2 后的直接宽化消费路径。
- [__bfloat162float](_bfloat162float.md)（`related`）：“__bfloat1622float2”处理将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。；“__bfloat162float”明确将bfloat16类型数据转换为浮点数，返回转换后的值。。实质衔接：float2 与 bfloat16x2 的反向转换说明向量打包路径，标量 bfloat16→float 用于核对每个分量的转换语义。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`related`）：“__bfloat1622float2”处理将bfloat16x2的两个分量分别转换为float，并填充到float2后返回。；“__float22bfloat162_rn”明确将float2类型数据遵循CAST_RINT模式转换为bfloat16x2类型，返回转换后的bfloat16x2类型数据。。实质衔接：float2 与 bfloat16x2 的反向转换说明向量打包路径，标量 bfloat16→float 用于核对每个分量的转换语义。
- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`related`）：__float2bfloat162_rn 与《__bfloat1622float2》的实质衔接是：单个 float 填充 bf16x2 的 RNE 转换与双 float、双标量打包、标量转换和反向解包共享分量顺序与舍入契约。
- [__float22bfloat162_rna_sat](_float22bfloat162_rna_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__bfloat1622float2》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__low2float](_low2float.md)（`same_topic`）：__low2float 与《__bfloat1622float2》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
<!-- cannbot:related:end -->
