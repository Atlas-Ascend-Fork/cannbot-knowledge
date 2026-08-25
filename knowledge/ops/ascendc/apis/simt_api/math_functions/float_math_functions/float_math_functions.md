---
type: API
title: float类型数学库函数
description: 提供float类型的三角、指数、对数、取整、比较及特殊运算等常用数学库函数列表。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/float_math_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# float类型数学库函数

提供 float 类型的完整数学运算库，涵盖三角函数（sinf、cosf、tanf 及反/双曲变体）、指数对数（expf、logf 及其变体）、开方与幂（sqrtf、powf、cbrtf）、误差函数（erff 系列）、贝塞尔函数（j0f、y0f 等）、浮点操作（fabsf、fmaf、fmodf）和取整判断（floorf、isnan、isinf 等）。函数以 `f` 后缀标识，遵循 C99 数学库语义。

<!-- cannbot:related:start -->
## 相关

- [Cbrtf](cbrtf.md)（`related`）：Cbrtf 与《float类型数学库函数》的实质衔接是：Cbrtf 与 Rcbrtf 是立方根/倒立方根成对数学语义，float 数学函数页给出头文件与标量调用边界。
- [数学函数powf](powf.md)（`related`）：焦点处理powf 在 float 数学库中的定位；float类型数学库函数正文界定“提供float类型的三角、指数、对数、取整、比较及特殊运算等常用数学库函数列表”。候选总览正文明确列出 powf 并提供其 C99 float 数学函数入口。
- [Remquof](remquof.md)（`same_topic`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；float类型数学库函数正文说明“提供 float 数学函数族入口，并在列表中明确收录 Remquof”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
<!-- cannbot:related:end -->
