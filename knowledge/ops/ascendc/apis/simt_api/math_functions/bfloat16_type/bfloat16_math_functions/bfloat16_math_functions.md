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

<!-- cannbot:related:start -->
## 相关

- [Hexp2](hexp2.md)（`same_topic`）：Hexp2 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hexp2 与 half、float 及双 lane Exp2 入口计算同一 2^x 任务，类型总览和各精度特殊值帮助选择返回宽度。
- [Hlog10](hlog10.md)（`same_topic`）：Hlog10 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hlog10 与 half、float、双 lane 和 Reg Log10 入口执行同一任务，类型总览用于对照特殊值和返回宽度。
- [Hrint](hrint.md)（`same_topic`）：Hrint 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Hsqrt](hsqrt.md)（`same_topic`）：Hsqrt 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
<!-- cannbot:related:end -->
