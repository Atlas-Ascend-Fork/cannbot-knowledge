---
type: API
title: half2类型数学库函数
description: 提供half2类型的数学库函数列表，包括指数、对数、三角函数、开方及取整等运算接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/half2_math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half2类型数学库函数

提供 half2 双分量向量类型的数学运算，以 `h2` 前缀标识，包括指数（h2exp、h2exp2、h2exp10）、对数（h2log、h2log2、h2log10）、三角（h2cos、h2sin）、双曲（h2tanh）、开方（h2sqrt、h2rsqrt）、倒数（h2rcp）和取整（h2rint、h2floor、h2ceil、h2trunc）。单条指令同时处理两个 half 分量，适合吞吐密集型计算。
