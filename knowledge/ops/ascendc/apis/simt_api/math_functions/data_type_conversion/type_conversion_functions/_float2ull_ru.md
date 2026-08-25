---
type: API
title: __float2ull_ru
description: 遵循CAST_CEIL模式，将浮点数转换为64位无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ull_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ull_ru

功能：遵循CAST_CEIL模式，将浮点数转换为64位无符号整数，返回转换后的值。

函数原型：unsigned long long int __float2ull_ru(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的64位无符号整数。特殊值：±0→0；nan→0；inf→18446744073709551615（ULLONG_MAX）；-inf→0；超出unsigned long long int范围的正值→18446744073709551615（ULLONG_MAX）；负数→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ll_ru](_float2ll_ru.md)（`related`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ll_ru正文界定“遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2uint_ru](_float2uint_ru.md)（`related`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2uint_ru正文界定“遵循CAST_CEIL模式，将浮点数转换为无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__ull2float_ru](_ull2float_ru.md)（`related`）：焦点处理float→uint64 的舍入模式与逆向转换；__ull2float_ru正文界定“遵循CAST_CEIL模式，将uint64类型数据转换为浮点数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ull_rd](_float2ull_rd.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_ru”明确遵循CAST_CEIL模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_rn](_float2ull_rn.md)（`same_topic`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ull_rn正文界定“遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ull_rna](_float2ull_rna.md)（`same_topic`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ull_rna正文界定“遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ull_rz](_float2ull_rz.md)（`same_topic`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ull_rz正文界定“遵循CAST_TRUNC模式，将浮点数转换为64位无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
<!-- cannbot:related:end -->
