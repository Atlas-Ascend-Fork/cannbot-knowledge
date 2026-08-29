---
type: API
title: GetDequantizeMaxMinTmpSize
description: 在host侧获取Dequantize接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetDequantizeMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetDequantizeMaxMinTmpSize

host侧Tiling接口，用于获取Dequantize接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetDequantizeMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Dequantize接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Dequantize](dequantize.md)（`related`）：“提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetDequantizeMaxMinTmpSize获取。”在 Kernel API 中指定 sizing 依赖；“host侧Tiling接口，用于获取Dequantize接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”给出 Host 到 Kernel 的参数交接。
- [GetDequantizeTmpBufferFactorSize](get_dequantize_tmp_buffer_factor_size.md)（`related`）：“参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Dequantize接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。”与“获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。”。两卡分别给出空间上下界和固定空间反推处理元素数的 factor，形成互补 Tiling 预算。
<!-- cannbot:related:end -->
