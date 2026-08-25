---
type: API
title: half2类型算术函数
description: 提供half2类型数据的加减乘除、绝对值、取负、乘加及ReLU等算术运算函数列表。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/half2_arithmetic_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half2类型算术函数

提供 half2 双分量向量类型的算术运算，包括加减乘除（__haddx2、__hsubx2、__hmulx2、__hdivx2）、绝对值（__habsx2）、取负（__hnegx2）、最大值（__hfmax2）及带 ReLU 的变体（__hfmax2_relu）。还包含复数乘加 __hcmadd，单条指令并行处理两个 half 分量，提升计算吞吐。
