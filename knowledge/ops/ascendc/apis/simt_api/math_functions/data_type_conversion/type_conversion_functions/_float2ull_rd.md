---
type: API
title: __float2ull_rd
description: 遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ull_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ull_rd

功能：遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。

函数原型：unsigned long long int __float2ull_rd(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的64位无符号整数。特殊值：±0→0；nan→0；inf→18446744073709551615（ULLONG_MAX）；-inf→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2ull_rd](../../half_type/half_precision_conversion_functions/_half2ull_rd.md)（`related`）：__half2ull_rd 与《__float2ull_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__float2ull_rn](_float2ull_rn.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_rn”明确遵循CAST_RINT模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_rna](_float2ull_rna.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_rna”明确遵循CAST_ROUND模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_ru](_float2ull_ru.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_ru”明确遵循CAST_CEIL模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
- [__float2ull_rz](_float2ull_rz.md)（`same_topic`）：“__float2ull_rd”处理遵循CAST_FLOOR模式，将浮点数转换为64位无符号整数，返回转换后的值。；“__float2ull_rz”明确遵循CAST_TRUNC模式，将浮点数转换为64位无符号整数，返回转换后的值。。实质衔接：这些接口保持 float→uint64 契约不变，只改变 floor/rint/round/ceil/trunc 舍入方式，直接支持按舍入语义选型。
<!-- cannbot:related:end -->
