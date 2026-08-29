---
type: API
title: half类型数学库函数
description: 提供half类型的数学库函数列表，包括指数、对数、三角函数、开方及取整等运算接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/half_math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half类型数学库函数

提供 half 类型的标量数学运算，以 `h` 前缀标识，涵盖指数（hexp、hexp2、hexp10）、对数（hlog、hlog2、hlog10）、三角（hcos、hsin）、双曲（htanh）、开方（hsqrt、hrsqrt）、倒数（hrcp）和取整（hrint、hfloor、hceil、htrunc）等常用函数。适用于 AICore 上 SIMT 编程模型的低精度计算。
