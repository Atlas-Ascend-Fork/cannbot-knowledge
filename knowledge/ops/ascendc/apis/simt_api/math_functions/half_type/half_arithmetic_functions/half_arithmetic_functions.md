---
type: API
title: half类型算术函数
description: 提供half类型数据的四则运算、取绝对值、取负与乘加运算接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/half_arithmetic_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half类型算术函数

提供 half 类型的标量算术运算，包括加减乘除（__hadd、__hsub、__hmul、__hdiv）、绝对值（__habs）、取负（__hneg）和乘加（__hfma）。还包含带 ReLU 激活的乘加变体 __hfma_relu，适用于 AICore 上的低精度推理计算。

<!-- cannbot:related:start -->
## 相关

- [__habs](_habs.md)（`related`）：半精度算术总页给出 HAbs 的支持平台、NaN 和舍入约束，是函数使用语境。
<!-- cannbot:related:end -->
