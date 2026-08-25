---
type: API
title: __ull2float_rna
description: 遵循CAST_ROUND模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_rna

功能：遵循CAST_ROUND模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_rna(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777218；33554431（2^25-1）→33554432；33554434（2^25+2）→33554436；18446744073709551615（ULLONG_MAX）→1.84467441e+19。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ull_rna](_float2ull_rna.md)（`related`）：__ull2float_rna 是 64 位无符号整数到 float 的反向转换，可与 focal 组成往返路径并评估大整数精度丢失。
- [__ull2half_rna](../../half_type/half_precision_conversion_functions/_ull2half_rna.md)（`related`）：__ull2half_rna 与《__ull2float_rna》的实质衔接是：uint64→half RNA 与其他舍入、有符号、bfloat16/float 目标变体共享大整数输入；UINT64 量化卡提供实际位宽约束。
- [__ll2float_rna](_ll2float_rna.md)（`same_topic`）：__ll2float_rna：所选转换保持ll→float或RNA语义，只切换有符号性、源位宽和RD/RN/RU/RZ舍入，能直接核对大整数不可精确表示时的方向。 目标卡《__ull2float_rna》补充：遵循CAST_ROUND模式，将uint64类型数据转换为浮点数，返回转换后的值。
- [__ull2float_rd](_ull2float_rd.md)（`same_topic`）：__ull2float_rd 与《__ull2float_rna》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__ull2float_rn](_ull2float_rn.md)（`same_topic`）：两卡同为 unsigned long long→float，分别采用 nearest-even 与 ties-away 的最近舍入规则。
- [__ull2float_ru](_ull2float_ru.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rna》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rz](_ull2float_rz.md)（`same_topic`）：两卡同为 uint64→float，分别采用 toward-zero 与 ties-away 的最近舍入。
<!-- cannbot:related:end -->
