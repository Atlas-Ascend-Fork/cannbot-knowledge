---
type: API
title: __half2ull_rz
description: 遵循CAST_TRUNC模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ull_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ull_rz

功能：遵循CAST_TRUNC模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。

函数原型：unsigned long long int __half2ull_rz(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的unsigned long long int类型数据。特殊值：±0→0；nan→0；inf→18446744073709551615（uint64_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2ull_rd](_half2ull_rd.md)（`related`）：__half2ull_rd 与《__half2ull_rz》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rn](_half2ull_rn.md)（`related`）：rz 使用 CAST_TRUNC，与 rn 在 1.5 等非整数输入上产生不同结果。
- [__bfloat162ull_rz](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ull_rz.md)（`same_topic`）：__bfloat162ull_rz 与《__half2ull_rz》的实质衔接是：这些转换保持 bfloat16→unsigned long long 并切换舍入模式，或保持 rz 改变源/目标符号与位宽，用于验证 CAST_TRUNC 的确切边界。
- [__half2ll_rz](_half2ll_rz.md)（`same_topic`）：__half2ll_rz 与《__half2ull_rz》的实质衔接是：这些转换保持 half→long long 并切换舍入，或保持 rz 改变源/目标符号；直接用于验证 CAST_TRUNC 的负数和边界行为。
<!-- cannbot:related:end -->
