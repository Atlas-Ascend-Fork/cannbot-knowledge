---
type: API
title: __half2float
description: 将half类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2float

功能：将half类型数据转换为浮点数，返回转换后的值。

函数原型：float __half2float(const half x)

参数：x（输入）源操作数。

返回值：输入转换成的浮点数。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2float](../../../../simd_api/c_api/vector_compute/asc_half2float.md)（`related`）：《__half2float》明确“将half类型数据转换为浮点数，返回转换后的值。”；它与《AscHalf2float》的“将half类型转化为float类型，无舍入模式。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscHalf2Float](../../../../simd_api/c_api/reg/data_type_convert/asc_half2float.md)（`same_topic`）：AscHalf2Float 与 __half2float 都执行无舍入的 half→float 扩展；前者按 mask 处理 Reg 向量，后者处理单个 SIMT 标量。
- [__half22float2](_half22float2.md)（`same_topic`）：__half2float 与《__half22float2》的衔接是：C Reg、C Vector 和 half2 转换入口都执行 half 到 float 的数值扩展，仅批宽与执行单元不同。
<!-- cannbot:related:end -->
