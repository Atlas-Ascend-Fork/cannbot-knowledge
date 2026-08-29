---
type: API
title: bfloat16类型数学库函数
description: bfloat16类型数学库函数集合，涵盖htanh、hexp、hlog、hcos、hsin、hsqrt等常用数学运算。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/bfloat16_math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16类型数学库函数

提供 bfloat16 类型的标量数学运算，涵盖指数（hexp、hexp2、hexp10）、对数（hlog、hlog2、hlog10）、三角（hcos、hsin）、双曲（htanh）、开方（hsqrt、hrsqrt）、倒数（hrcp）和取整（hrint、hfloor、hceil、htrunc）等常用函数。所有函数以 `h` 前缀标识，输入输出均为 bfloat16 标量，适用于 AICore 上的 SIMT 编程模型。
