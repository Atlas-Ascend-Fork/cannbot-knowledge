---
type: API
title: __half2ull_rn
description: 遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ull_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ull_rn

功能：遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。

函数原型：unsigned long long int __half2ull_rn(const half x)

参数：x（输入）源操作数。

返回值：遵循CAST_RINT模式，将half类型数据转换为usigned long long类型数据。特殊值：±0→0；0.5→0；1.5→2；nan→0；inf→18446744073709551615（uint64_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2ull_rd](_half2ull_rd.md)（`related`）：__half2ull_rd 与《__half2ull_rn》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rz](_half2ull_rz.md)（`related`）：rz 使用 CAST_TRUNC，与 rn 在 1.5 等非整数输入上产生不同结果。
- [__bfloat162ull_rn](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ull_rn.md)（`same_topic`）：__bfloat162ull_rn 与《__half2ull_rn》的实质衔接是：这些转换卡保持目标 unsigned long long 或舍入到最近的契约，仅改变 bfloat16 的舍入模式或源类型；有符号 long long 入口用于核对目标符号语义。
- [__half2ll_rn](_half2ll_rn.md)（`same_topic`）：__half2ll_rn 与《__half2ull_rn》的实质衔接是：这些转换保持 half→long long 并切换舍入模式，或保持 RINT 改变源/目标有无符号；可直接核对 rn 的边界与溢出行为。
- [__half2ull_rna](_half2ull_rna.md)（`same_topic`）：《__half2ull_rn》明确“遵循CAST_RINT模式，将half类型数据转换为unsigned long long类型数据，返回转换后的值。”；它与《__half2ull_rna》的“遵循CAST_ROUND模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
- [__half2ull_ru](_half2ull_ru.md)（`same_topic`）：两接口都将 half 转为 uint64，RU 向正无穷舍入、RN 取最近偶数；目标可用于验证负值、半整数和上界的舍入选择。
<!-- cannbot:related:end -->
