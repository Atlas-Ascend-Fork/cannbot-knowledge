---
type: API
title: GetFracMaxMinTmpSize
description: 在host侧获取Frac接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Frac_interface/GetFracMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetFracMaxMinTmpSize

host侧Tiling接口，用于获取Frac接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetFracMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource为是否允许修改源操作数输入空间；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Frac](frac.md)（`related`）：GetFracMaxMinTmpSize 返回的 min/max 是 Frac kernel sharedTmpBuffer 的正确性和性能边界，直接用于 host tiling 选值。
- [Frac接口](frac_interface.md)（`related`）：《GetFracMaxMinTmpSize》明确“在host侧获取Frac接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
