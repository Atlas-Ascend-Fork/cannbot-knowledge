---
type: API
title: __lowhigh2highlow
description: 将bfloat16x2_t输入数据的高低16位进行交换，返回交换后的bfloat16x2_t数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__lowhigh2highlow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __lowhigh2highlow

功能：将输入数据的高低16位进行交换并返回。

函数原型：bfloat16x2_t __lowhigh2highlow(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的高低16位进行交换的结果。特殊值：(0, -0)→(-0, 0)；(nan, 正常值)→(正常值, nan)；(inf, -inf)→(-inf, inf)；(ASCRT_MAX_NORMAL_BF16, -ASCRT_MAX_NORMAL_BF16)→(-ASCRT_MAX_NORMAL_BF16, ASCRT_MAX_NORMAL_BF16)；(nan, nan)→(nan, nan)。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2bfloat16](_high2bfloat16.md)（`related`）：交换后常需提取新的高分量，__high2bfloat16 提供标量读取路径并明确返回类型。
- [__lowhigh2highlow](../../half_type/half_precision_conversion_functions/_lowhigh2highlow.md)（`related`）：两接口都交换 packed 双元素的高低 16 位，分别处理 half2 与 bfloat16x2。
- [__highs2bfloat162](_highs2bfloat162.md)（`same_topic`）：《__highs2bfloat162》处理“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”。《__lowhigh2highlow》明确“将bfloat16x2_t输入数据的高低16位进行交换，返回交换后的bfloat16x2_t数据。”，可直接用于核对packed bfloat16 高低 lane 的构造、提取、交换及 half2 对应操作。
- [__low2float](_low2float.md)（`same_topic`）：__low2float 与《__lowhigh2highlow》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
<!-- cannbot:related:end -->
