---
type: API
title: Where（数学计算）
description: 根据指定的条件，从两个源操作数中选择元素，生成目标操作数。两个源操作数均可以是LocalTensor或标量。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Where_interface/Where.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Where

根据条件从两个源操作数中选择元素生成目标操作数，两个源操作数均可为LocalTensor或标量。仅Ascend 950PR/950DT支持。

函数原型：template <typename T, typename U, typename S, typename V> __aicore__ inline void Where(const LocalTensor<T>& dst, const U& src0, const S& src1, const LocalTensor<V>& condition, const uint32_t count)

模板参数T为目的操作数数据类型（支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t）；U、S为LocalTensor或标量类型，根据src0/src1自动推导，数据类型需与dst一致；V为条件数据类型（仅支持bool）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src0、src1为源操作数（标量或LocalTensor）；condition为条件操作数（bool类型LocalTensor）；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。
