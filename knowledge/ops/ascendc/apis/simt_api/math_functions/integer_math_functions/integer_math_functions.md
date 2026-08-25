---
type: API
title: 整型数学库函数
description: 提供整型数据的位操作、乘法、绝对差与平均值等数学运算接口。
tags: [task.lookup, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/integer_math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 整型数学库函数

提供整型的数学运算，包括绝对值（labs、llabs）、最大最小值（max、min、llmax 等）、高位乘法（__mulhi、__mul64hi）、位操作（__brev、__clz、__ffs、__popc）、字节置换（__byte_perm）、绝对差之和（__sad、__usad）和平均值（__hadd、__rhadd）。还包含 24 位和 32→64 位乘法扩展函数。

<!-- cannbot:related:start -->
## 相关

- [__mul64hi](_mul64hi.md)（`related`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；整型数学库函数正文界定“提供整型数据的位操作、乘法、绝对差与平均值等数学运算接口”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__umul64hi](_umul64hi.md)（`related`）：整型数学库函数说明提供整型数据的位操作、乘法、绝对差与平均值等数学运算接口。
<!-- cannbot:related:end -->
