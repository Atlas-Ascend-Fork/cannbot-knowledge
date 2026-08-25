---
type: API
title: __half2ll_rd
description: 遵循CAST_FLOOR模式，将half类型数据转换为long long类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ll_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ll_rd

功能：遵循CAST_FLOOR模式，将half类型数据转换为long long类型数据，返回转换后的值。

函数原型：long long int __half2ll_rd(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的long long类型数据。特殊值：±0→0；nan→0；inf→9223372036854775807（long long最大值）；-inf→-9223372036854775808（long long最小值）；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；1.5→1；-1.5→-2。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162ll_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ll_rd.md)（`related`）：bfloat16 源的同向转换具有不同精度范围。
- [__half2ull_rd](_half2ull_rd.md)（`related`）：__half2ull_rd 与《__half2ll_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ll_rn](_half2ll_rn.md)（`same_topic`）：__half2ll_rn 与《__half2ll_rd》的实质衔接是：这些转换保持 half→long long 并切换舍入模式，或保持 RINT 改变源/目标有无符号；可直接核对 rn 的边界与溢出行为。
- [__half2ll_rna](_half2ll_rna.md)（`same_topic`）：rd 使用 floor，rna 使用 ties-away；负分数如 -1.5 的方向差异直接影响整数结果。
- [__half2ll_ru](_half2ll_ru.md)（`same_topic`）：ru 提供向上舍入，与 rd 构成边界两端。
- [__half2ll_rz](_half2ll_rz.md)（`same_topic`）：__half2ll_rz 与《__half2ll_rd》的实质衔接是：这些转换保持 half→long long 并切换舍入，或保持 rz 改变源/目标符号；直接用于验证 CAST_TRUNC 的负数和边界行为。
<!-- cannbot:related:end -->
