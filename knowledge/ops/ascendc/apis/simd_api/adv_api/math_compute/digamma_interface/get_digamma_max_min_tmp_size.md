---
type: API
title: GetDigammaMaxMinTmpSize
description: 在host侧获取Digamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Digamma_interface/GetDigammaMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetDigammaMaxMinTmpSize

host侧Tiling接口，用于获取Digamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetDigammaMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Digamma接口保持一致；maxValue输出最大临时空间大小（超出不被使用，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Digamma](digamma.md)（`same_topic`）：Digamma说明按元素计算x的gamma函数的对数导数。
- [Digamma接口](digamma_interface.md)（`same_topic`）：Digamma 的 sharedTmpBuffer 必须先在 Host 侧按 shape 取得最大/最小临时空间并传入 Tiling。
- [GetDigammaTmpBufferFactorSize](get_digamma_tmp_buffer_factor_size.md)（`same_topic`）：GetDigammaTmpBufferFactorSize：该因子接口与 Digamma计算及同名 MaxMinTmpSize共同闭合 host预算公式和 kernel sharedTmpBuffer；接口页给出两种重载与复用约束。 目标卡《GetDigammaMaxMinTmpSize》补充：在host侧获取Digamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
<!-- cannbot:related:end -->
