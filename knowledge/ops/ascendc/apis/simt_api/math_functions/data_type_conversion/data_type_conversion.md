---
type: API
title: 数据类型转换
description: SIMT数据类型转换接口集合，涵盖概述和类型转换函数。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/data_type_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据类型转换

提供 SIMT API 数据类型转换能力，包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行：整型转整型和浮点转整型遵循 CAST_TRUNC，整型转浮点和浮点转浮点遵循 CAST_RINT。

显式转换通过调用类型转换 API 主动完成，转换结果受舍入模式和饱和模式影响。宽范围转窄范围时：浮点转整型超出范围取最大/最小值，nan 转 0；整型转浮点超出范围取对应符号 inf；浮点转浮点超出范围取对应符号 inf，nan 保持 nan。

<!-- cannbot:related:start -->
## 相关

- [half类型精度转换函数](../half_type/half_precision_conversion_functions/half_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《数据类型转换》说明SIMT数据类型转换接口集合，涵盖概述和类型转换函数。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [类型转换函数](type_conversion_functions/type_conversion_functions.md)（`related`）：类型转换函数页把 overview 的规则映射到 float/int/uint/ll/ull 各舍入模式的显式函数，是从规则到具体调用的入口。
- [数据类型转换概述](overview.md)（`same_topic`）：overview 解释隐式/显式转换、舍入和饱和如何决定结果，是本索引卡简述的完整语义契约。
<!-- cannbot:related:end -->
