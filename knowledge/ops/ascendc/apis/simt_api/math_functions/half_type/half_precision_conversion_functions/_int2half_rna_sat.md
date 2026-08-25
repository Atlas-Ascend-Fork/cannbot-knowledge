---
type: API
title: __int2half_rna_sat
description: 将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2half_rna_sat

功能：将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。

函数原型：half __int2half_rna_sat(const int x)

参数：x（输入）源操作数。

返回值：遵循CAST_ROUND模式，将输入int32数据转换成的half数据。特殊值：0→0；2147483647（int32_t最大值）→ASCRT_MAX_NORMAL_FP16；-2147483648（int32_t最小值）→-ASCRT_MAX_NORMAL_FP16。

约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__int2half_rd](_int2half_rd.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rd》明确提供“遵循CAST_FLOOR模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rd_sat](_int2half_rd_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rd_sat》明确提供“按照CAST_FLOOR模式将int32类型数据转换为half类型数据。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rn](_int2half_rn.md)（`same_topic`）：《__int2half_rn》的任务是“遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。”。《__int2half_rna_sat》具体提供“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”，它直接用于int32→half 的舍入与饱和组合选择。
- [__int2half_rn_sat](_int2half_rn_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rn_sat》明确提供“将int32类型数据按照CAST_RINT模式转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rna](_int2half_rna.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rna》明确提供“遵循CAST_ROUND模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_ru](_int2half_ru.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_ru》明确提供“遵循CAST_CEIL模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_ru_sat](_int2half_ru_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_ru_sat》明确提供“将int32类型数据转换为half类型数据，并遵循CAST_CEIL模式，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rz](_int2half_rz.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rz》明确提供“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
- [__int2half_rz_sat](_int2half_rz_sat.md)（`same_topic`）：《__int2half_rna_sat》处理“将int32类型数据转换为half类型数据，并遵循CAST_ROUND模式，返回转换后的值。”。《__int2half_rz_sat》明确提供“遵循CAST_TRUNC模式，将int32类型数据转换为half类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入int32 到 half 的舍入与 saturation 组合选择。
<!-- cannbot:related:end -->
