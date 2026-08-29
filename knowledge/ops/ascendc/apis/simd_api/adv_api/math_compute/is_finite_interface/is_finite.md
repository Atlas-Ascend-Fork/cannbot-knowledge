---
type: API
title: IsFinite
description: 按元素判断输入浮点数是否非NAN、非±INF，输出结果为浮点数或布尔值，支持half、bfloat16_t、float数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsFinite_interface/IsFinite.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsFinite

按元素判断输入浮点数是否非NAN且非±INF。输出为浮点类型时，非NAN/非±INF位置结果为1，反之为0；输出为bool类型时，对应位置为true/false。仅Ascend 950PR/950DT支持。

函数原型：template<typename T, typename U> __aicore__ inline void IsFinite(const LocalTensor<U>& dst, const LocalTensor<T>& src, uint32_t calCount)

模板参数T为源操作数数据类型（支持half/bfloat16_t/float）；U为目的操作数数据类型（支持bool/half/bfloat16_t/float）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数；calCount为参与计算元素个数。

支持的输入输出数据类型组合：half-half/bool、float-float/bool、bfloat16_t-bfloat16_t/bool（dst类型与src一致或为bool）。约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。
