---
type: API
title: GetTanhMaxMinTmpSize
description: 在host侧获取Tanh接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tanh_interface/GetTanhMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTanhMaxMinTmpSize

host侧Tiling接口，用于获取Tanh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetTanhMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Tanh接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Tanh](tanh.md)（`related`）：Host 接口说明“host侧Tiling接口，用于获取Tanh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；Tanh 卡明确“临时空间大小通过GetTanhMaxMinTmpSize获取。”，两端形成 Tanh sharedTmpBuffer 的容量选择与调用链，但 Host Tiling 规划和 Kernel 双曲正切计算是两个主题。
<!-- cannbot:related:end -->
