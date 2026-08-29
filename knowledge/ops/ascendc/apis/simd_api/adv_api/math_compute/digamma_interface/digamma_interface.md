---
type: API
title: Digamma接口
description: 按元素计算x的gamma函数的对数导数（Digamma函数），并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Digamma_interface/Digamma_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Digamma接口

按元素计算 x 的 gamma 函数对数导数，即 Digamma 函数。该接口族包含三个成员：Digamma 为主计算接口，按元素求解输入张量的 Digamma 值；GetDigammaMaxMinTmpSize 用于根据输入数据量和数据类型查询所需临时空间的最大与最小值；GetDigammaTmpBufferFactorSize 用于获取临时空间的倍数因子，便于按既定公式推算 Tiling 所需 workspace 大小。
调用时需先通过 GetDigammaMaxMinTmpSize 或 GetDigammaTmpBufferFactorSize 估算临时空间，再申请 LocalTensor 并传入 Digamma 执行计算。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。
