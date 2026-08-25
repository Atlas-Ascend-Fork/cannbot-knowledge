---
type: API
title: __float2ull_rn
description: 遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ull_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ull_rn

功能：遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值。

函数原型：unsigned long long int __float2ull_rn(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的64位无符号整数。特殊值：±0→0；nan→0；inf→18446744073709551615（ULLONG_MAX）；-inf→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2ll_rn](_float2ll_rn.md)（`related`）：__float2ll_rn 采用同一 CAST_RINT 舍入并保持 64 位宽度，目标有符号边界与 ull 版本不同。
- [__float2uint_rn](_float2uint_rn.md)（`related`）：__float2uint_rn 保持无符号与 RINT 语义，但目标缩为 32 位，可用于按范围选择转换宽度。
- [__bfloat162ull_rn](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ull_rn.md)（`same_topic`）：__bfloat162ull_rn 与《__float2ull_rn》的实质衔接是：这些转换卡保持目标 unsigned long long 或舍入到最近的契约，仅改变 bfloat16 的舍入模式或源类型；有符号 long long 入口用于核对目标符号语义。
- [__float2ull_rd](_float2ull_rd.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_rn”明确遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_rna](_float2ull_rna.md)（`same_topic`）：__float2ull_rn 提供最近偶数舍入，与 focal 的 CAST_ROUND 形成同目标类型的舍入策略选择。
- [__float2ull_ru](_float2ull_ru.md)（`same_topic`）：焦点处理float→uint64 的舍入模式与逆向转换；__float2ull_rn正文界定“遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值”。候选保持 float→uint64 目标或同一 CEIL 规则，覆盖其他舍入模式和逆转换。
- [__float2ull_rz](_float2ull_rz.md)（`same_topic`）：__float2ull_rz 保持 float→uint64_t 目标不变，仅采用截断舍入。
<!-- cannbot:related:end -->
