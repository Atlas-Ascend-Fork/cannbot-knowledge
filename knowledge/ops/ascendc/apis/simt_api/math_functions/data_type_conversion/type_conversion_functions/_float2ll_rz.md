---
type: API
title: __float2ll_rz
description: 遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ll_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ll_rz

功能：遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。

函数原型：long long int __float2ll_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的64位有符号整数。特殊值：±0→0；nan→0；inf→9223372036854775807（INT64_MAX）；-inf→-9223372036854775808（INT64_MIN）；超出int64范围的正值→9223372036854775807（INT64_MAX）；超出int64范围的负值→-9223372036854775808（INT64_MIN）。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Reg int32→int64 Cast 源目 VL 错配留空索引](../../../../../runbooks/precision/int32_to_int64_reg_cast_must_respect_destination_lane_width.md)（`exemplifies`）：__float2ll_rz 与《Reg int32→int64 Cast 源目 VL 错配留空索引》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__bfloat162ll_rz](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ll_rz.md)（`related`）：__float2ll_rz 与《__bfloat162ll_rz》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__float2ull_rz](_float2ull_rz.md)（`related`）：__float2ll_rz 与《__float2ull_rz》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__float2ll_rd](_float2ll_rd.md)（`same_topic`）：__float2ll_rz 与《__float2ll_rd》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__float2ll_rn](_float2ll_rn.md)（`same_topic`）：__float2ll_rz 与《__float2ll_rn》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__float2ll_rna](_float2ll_rna.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_rz》说明遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2ll_ru](_float2ll_ru.md)（`same_topic`）：__float2ll_rz 与《__float2ll_ru》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
- [__half2ll_rz](../../half_type/half_precision_conversion_functions/_half2ll_rz.md)（`same_topic`）：__half2ll_rz 与《__float2ll_rz》的实质衔接是：这些转换保持 half→long long 并切换舍入，或保持 rz 改变源/目标符号；直接用于验证 CAST_TRUNC 的负数和边界行为。
- [__ll2float_rz](_ll2float_rz.md)（`same_topic`）：__float2ll_rz 与《__ll2float_rz》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
<!-- cannbot:related:end -->
