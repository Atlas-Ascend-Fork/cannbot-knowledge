---
type: API
title: GetQuantizeMaxMinTmpSize
description: 在host侧获取Quantize接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetQuantizeMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetQuantizeMaxMinTmpSize

host侧Tiling接口，用于获取Quantize接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetQuantizeMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Quantize接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Quantize](quantize.md)（`related`）：Quantize 的 sharedTmpBuffer 大小需由 Host 侧 max/min 查询按 shape 和 dtype 预算。
- [GetQuantizeTmpBufferFactorSize](get_quantize_tmp_buffer_factor_size.md)（`same_topic`）：GetQuantizeTmpBufferFactorSize 与《GetQuantizeMaxMinTmpSize》的实质衔接是：GetQuantizeTmpBufferFactorSize 用可用 UB 反推 Quantize 的单次元素数，GetQuantizeMaxMinTmpSize 给出另一种 Host 侧空间选择，Quantize kernel 是两类查询结果的直接消费方。
<!-- cannbot:related:end -->
