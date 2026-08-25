---
type: API
title: __uint2float_rn
description: 遵循CAST_RINT模式，将uint32类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__uint2float_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2float_rn

功能：遵循CAST_RINT模式，将uint32类型数据转换为浮点数，返回转换后的值。

函数原型：float __uint2float_rn(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的浮点数。特殊值：0→0；16777217→ASCRT_TWO_TO_24_F；16777219→16777220；4294967295 (UINT32_MAX)→ASCRT_TWO_TO_32_F。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint_as_float](_uint_as_float.md)（`related`）：uint2float 是数值转换并可能舍入，和 uint_as_float 的 bitcast 语义必须明确区分。
- [__uint2float_rd](_uint2float_rd.md)（`same_topic`）：__uint2float_rd 与《__uint2float_rn》的衔接是：候选覆盖 uint 到 float 的 rn/rd/ru/rz 变体及相邻整数宽度，直接用于核对 focal 的向下舍入和输入范围边界。
- [__uint2float_rna](_uint2float_rna.md)（`same_topic`）：rn 与 rna 都做 uint→float 最近舍入，但 tie 处理不同；半值边界必须按参考契约选择。
- [__uint2float_ru](_uint2float_ru.md)（`same_topic`）：__uint2float_ru 与《__uint2float_rn》的实质衔接是：候选覆盖 uint32→float 的其他舍入方向、signed int 与 uint64 输入；它们直接对照 2^24+1 等不可精确表示整数在 ru 下的选择。
- [__uint2float_rz](_uint2float_rz.md)（`same_topic`）：两卡均为 uint32→float，仅 rn 与 trunc 舍入不同；在不能精确表示的整数上可直接按误差方向选型。
<!-- cannbot:related:end -->
