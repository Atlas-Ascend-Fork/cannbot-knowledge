---
type: API
title: half类型精度转换函数
description: 提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/half_precision_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half类型精度转换函数

提供 half 与 float、bfloat16、int、uint、ll、ull 等类型之间的双向精度转换，支持 rn、rz、rd、ru、rna 五种舍入模式及 ro 舍入变体，部分函数提供 _sat 饱和版本。还包含 half2 向量类型的拆分与组合函数（__high2half、__low2half、__halves2half2 等）和位级重解释函数 __ushort_as_half。

<!-- cannbot:related:start -->
## 相关

- [核函数运行验证时算子存在精度问题](../../../../../guides/programming_guide/appendix/faq/kernel_precision_issue.md)（`explains`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《核函数运行验证时算子存在精度问题》说明在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [SIMT接口精度标准汇总](../../../../appendix/simt_interface_precision_standard_summary.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《SIMT接口精度标准汇总》说明本节按照数据类型和接口类型对SIMT浮点计算接口进行精度标准的分类汇总。对于非软仿接口，给出对应硬件指令的精度标准；对于软仿接口，由于软仿程度较低且使用到的硬件指令较少，给出其所用硬件指令的综合性精度标准。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [bfloat16类型精度转换函数](../../bfloat16_type/bfloat16_precision_conversion_functions/bfloat16_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《bfloat16类型精度转换函数》说明bfloat16类型精度转换函数列表，包含bfloat16与float、half、int、uint、ull等类型间的相互转换。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [数据类型转换](../../data_type_conversion/data_type_conversion.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《数据类型转换》说明SIMT数据类型转换接口集合，涵盖概述和类型转换函数。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [类型转换函数](../../data_type_conversion/type_conversion_functions/type_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [精度转换（数据结构）](../../../../simd_api/basic_api/data_structures/precision_conversion.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《精度转换（数据结构）》说明在了解不同类型之间的精度转换规则之前，需先了解二进制的精度舍入规则。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [__ushort_as_half](_ushort_as_half.md)（`same_topic`）：__ushort_as_half 与《half类型精度转换函数》的实质衔接是：__ushort_as_half 是位重解释而非数值转换；bfloat16 对应入口、half 类型转换总览和 low-half 提取帮助区分相同位模式的读取方式。
<!-- cannbot:related:end -->
