---
type: API
title: __half2ull_ru
description: 遵循CAST_CEIL模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ull_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ull_ru

功能：遵循CAST_CEIL模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。

函数原型：unsigned long long int __half2ull_ru(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_CEIL模式转换成的unsigned long long int类型数据。特殊值：±0→0；nan→0；inf→18446744073709551615（uint64_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162ull_ru](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ull_ru.md)（`related`）：half 源的 ru 版本目标和舍入方向相同，但源精度/范围不同。
- [__half2int_ru](_half2int_ru.md)（`related`）：__half2int_ru 与《__half2ull_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2ull_rd](_half2ull_rd.md)（`related`）：__half2ull_rd 与《__half2ull_ru》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rn](_half2ull_rn.md)（`same_topic`）：两接口都将 half 转为 uint64，RU 向正无穷舍入、RN 取最近偶数；目标可用于验证负值、半整数和上界的舍入选择。
- [__half2ull_rna](_half2ull_rna.md)（`same_topic`）：《__half2ull_ru》明确“遵循CAST_CEIL模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。”；它与《__half2ull_rna》的“遵循CAST_ROUND模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
