---
type: API
title: GetErfcMaxMinTmpSize
description: 在host侧获取Erfc接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erfc_interface/GetErfcMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetErfcMaxMinTmpSize

host侧Tiling接口，用于获取Erfc接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetErfcMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Erfc接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Erfc](erfc.md)（`related`）：Erfc 的 sharedTmpBuffer 需由 Host tiling 预算，GetErfcMaxMinTmpSize 给出最小/最大值并说明区间内空间越大性能越好，是计算接口的直接前置。
- [Erfc接口](erfc_interface.md)（`same_topic`）：Erfc接口 与《GetErfcMaxMinTmpSize》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
- [GetErfcTmpBufferFactorSize](get_erfc_tmp_buffer_factor_size.md)（`same_topic`）：MaxMin 从 shape 给出 Erfc sharedTmpBuffer 合法区间，FactorSize 从固定剩余空间反推 currentShapeSize；二者是同一临时空间的正向预算和反向容量计算。
<!-- cannbot:related:end -->
