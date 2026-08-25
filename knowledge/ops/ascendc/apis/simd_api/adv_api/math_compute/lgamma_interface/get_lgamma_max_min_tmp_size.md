---
type: API
title: GetLgammaMaxMinTmpSize
description: 在host侧获取Lgamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/GetLgammaMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLgammaMaxMinTmpSize

host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLgammaMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Lgamma接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Lgamma接口](lgamma_interface.md)（`related`）：Lgamma 的显式 sharedTmpBuffer 需按该 Host 查询的最小/最大空间范围分配。
- [GetLgammaTmpBufferFactorSize](get_lgamma_tmp_buffer_factor_size.md)（`same_topic`）：Lgamma factor 查询用 maxLiveNodeCount/extraBuf 反推固定空间下的处理量，MaxMin 查询则给出同一 Lgamma 接口的可预留空间上下界，两者共同闭合 Tiling 预算。
- [Lgamma](lgamma.md)（`same_topic`）：《Lgamma》处理“按元素计算x的gamma函数的绝对值并求自然对数”。《GetLgammaMaxMinTmpSize》明确“在host侧获取Lgamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，可直接用于核对Lgamma Kernel、临时空间查询与标量 lgammaf 的同一计算合同。
<!-- cannbot:related:end -->
