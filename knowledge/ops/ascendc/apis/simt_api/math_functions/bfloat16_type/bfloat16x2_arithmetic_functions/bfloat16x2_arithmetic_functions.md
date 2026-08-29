---
type: API
title: bfloat16x2类型算术函数
description: bfloat16x2类型算术函数列表，包含加减乘除、绝对值、负值、乘加及复数乘加等运算。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/bfloat16x2_arithmetic_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16x2类型算术函数

提供 bfloat16x2 双分量向量类型的算术运算，包括加减乘除（__haddx2、__hsubx2、__hmulx2、__hdivx2）、绝对值（__habsx2）、取负（__hnegx2）、逐分量乘加（__hfmax2，可按 `__hfma` + `x2` 理解）及带 ReLU 的变体（__hfmax2_relu）。还包含复数乘加 __hcmadd，支持在单条指令中完成两个 bfloat16 分量的并行运算。
