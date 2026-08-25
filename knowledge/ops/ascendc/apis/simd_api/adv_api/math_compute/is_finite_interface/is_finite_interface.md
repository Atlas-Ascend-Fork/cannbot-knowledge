---
type: API
title: IsFinite
description: IsFinite数学计算接口集合，用于判断数据是否为有限值。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsFinite_interface/IsFinite_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsFinite接口

IsFinite 按元素判断输入浮点数是否非 NaN、非 ±INF。对于有限值输入，输出浮点类型时对应位置为 1，输出 bool 类型时为 true；否则为 0 或 false。

接口为模板函数，源操作数支持 half、bfloat16_t、float，目的操作数支持 bool、half、bfloat16_t、float。通过 `calCount` 指定计算元素个数。不支持源操作数与目的操作数地址重叠。仅 Ascend 950PR/Ascend 950DT 支持。
