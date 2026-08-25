---
type: API
title: __low2float
description: 将bfloat16x2_t输入数据的低16位转换为float类型并返回结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__low2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __low2float

功能：将输入数据的低16位转换为浮点数并返回结果。

函数原型：float __low2float(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的低16位转换为浮点数的结果。特殊值：±0→±0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_BF16→ASCRT_MAX_NORMAL_BF16；-ASCRT_MAX_NORMAL_BF16→-ASCRT_MAX_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__low2float](../../half_type/half_precision_conversion_functions/_low2float.md)（`related`）：两接口都从 packed 16 位双元素中提取低 lane 并升为 float，分别对应 half2 与 bfloat16x2。
- [__bfloat1622float2](_bfloat1622float2.md)（`same_topic`）：__low2float 与《__bfloat1622float2》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
- [__bfloat162float](_bfloat162float.md)（`same_topic`）：__low2float 与《__bfloat162float》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
- [__high2float](_high2float.md)（`same_topic`）：__low2float 与《__high2float》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
- [__lowhigh2highlow](_lowhigh2highlow.md)（`same_topic`）：__low2float 与《__lowhigh2highlow》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
<!-- cannbot:related:end -->
