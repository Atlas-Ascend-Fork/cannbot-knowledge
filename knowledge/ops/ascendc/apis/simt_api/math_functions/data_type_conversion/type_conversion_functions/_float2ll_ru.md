---
type: API
title: __float2ll_ru
description: 遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ll_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ll_ru

功能：遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值。

函数原型：long long int __float2ll_ru(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的64位有符号整数。特殊值：±0→0；nan→0；inf→9223372036854775807（INT64_MAX）；-inf→-9223372036854775808（INT64_MIN）。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ull_ru](_float2ull_ru.md)（`related`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ll_ru正文界定“遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ll_rd](_float2ll_rd.md)（`same_topic`）：RD 与 focal 的 RU 都转换 float→int64，分别向下和向上，形成 floor/ceil 选择。
- [__float2ll_rn](_float2ll_rn.md)（`same_topic`）：__float2ll_rn 与《__float2ll_ru》的实质衔接是：float→int64 RN 与 RD/RNA/RU/RZ、无符号及 half/bfloat16 输入变体共享饱和范围和特殊值，只改变舍入方向或输入精度。
- [__float2ll_rna](_float2ll_rna.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_ru》说明遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2ll_rz](_float2ll_rz.md)（`same_topic`）：__float2ll_rz 与《__float2ll_ru》的实质衔接是：float→int64 RZ 与其他舍入、无符号和 half/bfloat16 变体共享饱和范围；Reg lane 错配卡验证 32→64 位宽变化的存储边界。
<!-- cannbot:related:end -->
