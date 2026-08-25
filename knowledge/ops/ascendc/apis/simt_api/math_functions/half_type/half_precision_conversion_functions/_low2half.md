---
type: API
title: __low2half
description: 返回输入数据的低16位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__low2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __low2half

功能：返回输入数据的低16位。

函数原型：half __low2half(const half2 x)

参数：x（输入）源操作数。

返回值：输入数据的低16位。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→ASCRT_MIN_DENORM_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2half](_high2half.md)（`related`）：__high2half 提取同一 half2 的高 16 位，与 low 接口成对用于拆解两个分量。
- [__low2float](_low2float.md)（`related`）：__low2float 同样读取 half2 低 16 位，但进行数值提升到 float；只取位域与取后转换不可混同。
- [__ushort_as_half](_ushort_as_half.md)（`related`）：__ushort_as_half 与《__low2half》的实质衔接是：__ushort_as_half 是位重解释而非数值转换；bfloat16 对应入口、half 类型转换总览和 low-half 提取帮助区分相同位模式的读取方式。
- [__low2half2](_low2half2.md)（`same_topic`）：__low2half2 与《__low2half》的实质衔接是：low2half 与 lows2half2 分别说明低 half 的标量提取、复制和双输入拼装语义。
<!-- cannbot:related:end -->
