---
type: API
title: __int2half_ru
description: 遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2half_ru

功能：遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __int2half_ru(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的half类型数据。特殊值：0→0；ASCRT_MAX_NORMAL_FP16→inf；-ASCRT_MAX_NORMAL_FP16→-inf；2049→2050；-2049→-2048。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2half_rd](_int2half_rd.md)（`related`）：RU 与 RD 分别向正无穷和负无穷取整同一 int→half 转换，决定非精确表示时的方向。
- [__int2half_rn](_int2half_rn.md)（`same_topic`）：《__int2half_rn》的任务是“遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。”。《__int2half_ru》具体提供“遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。”，它直接用于int32→half 的舍入与饱和组合选择。
- [__int2half_rna_sat](_int2half_rna_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_ru》明确提供“遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_ru_sat](_int2half_ru_sat.md)（`same_topic`）：两者都是 int32→half、CAST_CEIL；非 sat 版本揭示 focal 名称中的 sat 在 SIMT 无法设置 CTRL 时实际不生效，数值行为应按非饱和边界验证。
- [__int2half_rz](_int2half_rz.md)（`same_topic`）：《__int2half_rz》处理“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”。《__int2half_ru》提供“遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其具体合同或探针直接接入int32 到 half 的 TRUNC 与其他舍入/饱和组合选择。
<!-- cannbot:related:end -->
