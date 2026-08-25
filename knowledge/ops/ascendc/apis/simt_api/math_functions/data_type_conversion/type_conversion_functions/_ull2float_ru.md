---
type: API
title: __ull2float_ru
description: 遵循CAST_CEIL模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_ru

功能：遵循CAST_CEIL模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_ru(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777218；18446744073709551615（ULLONG_MAX）→1.84467441e+19。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ull_ru](_float2ull_ru.md)（`related`）：焦点处理float→uint64 的舍入模式与逆向转换；__ull2float_ru正文界定“遵循CAST_CEIL模式，将uint64类型数据转换为浮点数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__ull2bfloat16_ru](../../bfloat16_type/bfloat16_precision_conversion_functions/_ull2bfloat16_ru.md)（`related`）：__ull2float_ru 与《__ull2bfloat16_ru》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2half_ru](../../half_type/half_precision_conversion_functions/_ull2half_ru.md)（`related`）：__ull2float_ru 与《__ull2half_ru》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ll2float_ru](_ll2float_ru.md)（`same_topic`）：__ull2float_ru 与《__ll2float_ru》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__uint2float_ru](_uint2float_ru.md)（`same_topic`）：__ull2float_ru 与《__uint2float_ru》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rd](_ull2float_rd.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rd》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rn](_ull2float_rn.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rn》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rna](_ull2float_rna.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rna》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rz](_ull2float_rz.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rz》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
<!-- cannbot:related:end -->
