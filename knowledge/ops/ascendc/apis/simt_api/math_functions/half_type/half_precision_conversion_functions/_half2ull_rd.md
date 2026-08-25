---
type: API
title: __half2ull_rd
description: 遵循CAST_FLOOR模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ull_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ull_rd

功能：遵循CAST_FLOOR模式，将half类型数据转换为unsigned long long int类型数据，返回转换后的值。

函数原型：unsigned long long int __half2ull_rd(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的unsigned long long int类型数据。特殊值：±0→0；nan→0；inf→18446744073709551615（uint64_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162ll_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ll_rd.md)（`related`）：__half2ull_rd 与《__bfloat162ll_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__bfloat162ull_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ull_rd.md)（`related`）：__half2ull_rd 与《__bfloat162ull_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__float2ll_rd](../../data_type_conversion/type_conversion_functions/_float2ll_rd.md)（`related`）：__half2ull_rd 与《__float2ll_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__float2ull_rd](../../data_type_conversion/type_conversion_functions/_float2ull_rd.md)（`related`）：__half2ull_rd 与《__float2ull_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2int_rd](_half2int_rd.md)（`related`）：__half2ull_rd 与《__half2int_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ll_rd](_half2ll_rd.md)（`related`）：__half2ull_rd 与《__half2ll_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2uint_rd](_half2uint_rd.md)（`related`）：__half2ull_rd 与《__half2uint_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rn](_half2ull_rn.md)（`related`）：__half2ull_rd 与《__half2ull_rn》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rna](_half2ull_rna.md)（`related`）：__half2ull_rd 与《__half2ull_rna》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_ru](_half2ull_ru.md)（`related`）：__half2ull_rd 与《__half2ull_ru》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__half2ull_rz](_half2ull_rz.md)（`related`）：__half2ull_rd 与《__half2ull_rz》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__ull2float_rd](../../data_type_conversion/type_conversion_functions/_ull2float_rd.md)（`related`）：__half2ull_rd 与《__ull2float_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
<!-- cannbot:related:end -->
