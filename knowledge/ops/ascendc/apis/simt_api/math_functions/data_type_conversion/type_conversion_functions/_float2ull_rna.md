---
type: API
title: __float2ull_rna
description: 遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ull_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ull_rna

功能：遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值。

函数原型：unsigned long long int __float2ull_rna(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的64位无符号整数。特殊值：±0→0；nan→0；inf→18446744073709551615（ULLONG_MAX）；-inf→0；负数→0；超出unsigned long long int范围的正值→18446744073709551615（ULLONG_MAX）。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2uint_rna](_float2uint_rna.md)（`related`）：__float2uint_rna 与 focal 使用同一 CAST_ROUND 从 float 转无符号整数，区别是 32 位与 64 位目标范围。
- [__ull2float_rna](_ull2float_rna.md)（`related`）：__ull2float_rna 是 64 位无符号整数到 float 的反向转换，可与 focal 组成往返路径并评估大整数精度丢失。
- [__float2ull_rd](_float2ull_rd.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_rna”明确遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_rn](_float2ull_rn.md)（`same_topic`）：__float2ull_rn 提供最近偶数舍入，与 focal 的 CAST_ROUND 形成同目标类型的舍入策略选择。
- [__float2ull_ru](_float2ull_ru.md)（`same_topic`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ull_rna正文界定“遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ull_rz](_float2ull_rz.md)（`same_topic`）：__float2ull_rz 直接向零截断，是 focal 在索引转换等不希望四舍五入场景中的替代模式。
<!-- cannbot:related:end -->
