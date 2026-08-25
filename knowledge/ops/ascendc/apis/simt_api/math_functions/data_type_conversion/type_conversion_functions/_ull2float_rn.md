---
type: API
title: __ull2float_rn
description: 遵循CAST_RINT模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_rn

功能：遵循CAST_RINT模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_rn(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的浮点数。特殊值：16777217 (2^24+1)→16777216.0；33554433 (2^25+1)→33554432.0；4294967295 (UINT32_MAX)→4294967296.0；18446744073709551615 (UINT64_MAX)→1.84467441e+19。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2float_rd](_ull2float_rd.md)（`same_topic`）：__ull2float_rd 与《__ull2float_rn》的实质衔接是：这些转换保持 ull 到 float 的源目类型并改变舍入模式；ll/uint 的 rd 入口用于核对有符号性和源位宽对向下舍入结果的影响。
- [__ull2float_rna](_ull2float_rna.md)（`same_topic`）：两卡同为 unsigned long long→float，分别采用 nearest-even 与 ties-away 的最近舍入规则。
- [__ull2float_ru](_ull2float_ru.md)（`same_topic`）：__ull2float_ru 与《__ull2float_rn》的实质衔接是：这些接口以 ull→float 为核心并切换舍入方向，ll/uint 入口验证源有无符号和位宽，ull→half/bfloat16 则保持 CAST_CEIL 但改变目标精度。
- [__ull2float_rz](_ull2float_rz.md)（`same_topic`）：两卡同为 unsigned long long→float，rn 取最近，rz 向零截断到可表示值。
<!-- cannbot:related:end -->
