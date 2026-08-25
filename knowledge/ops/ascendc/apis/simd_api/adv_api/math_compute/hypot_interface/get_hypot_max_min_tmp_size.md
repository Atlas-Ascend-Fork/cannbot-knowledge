---
type: API
title: GetHypotMaxMinTmpSize
description: 在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Hypot_interface/GetHypotMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetHypotMaxMinTmpSize

host侧Tiling接口，用于获取Hypot接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetHypotMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Hypot](hypot.md)（`related`）：The query determines the minimum and maximum temporary buffer accepted by the Hypot kernel call.
- [Hypot接口](hypot_interface.md)（`related`）：《GetHypotMaxMinTmpSize》明确“在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《Hypot接口》的“按元素计算两个浮点数平方和的平方根，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetHypotTmpBufferFactorSize](get_hypot_tmp_buffer_factor_size.md)（`same_topic`）：《GetHypotTmpBufferFactorSize》明确“获取Hypot接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”；它与《GetHypotMaxMinTmpSize》的“在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
