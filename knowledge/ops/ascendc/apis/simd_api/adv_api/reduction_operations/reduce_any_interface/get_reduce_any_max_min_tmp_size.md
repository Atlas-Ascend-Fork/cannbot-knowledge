---
type: API
title: GetReduceAnyMaxMinTmpSize
description: 在host侧获取ReduceAny接口计算所需的最大和最小临时空间大小，用于选择合适的空间作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAny_interface/GetReduceAnyMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceAnyMaxMinTmpSize

host侧Tiling接口，用于获取ReduceAny接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceAnyMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceAny接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ReduceAny](reduce_any.md)（`related`）：“host侧Tiling接口，用于获取ReduceAny接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”明确给出左端事实；“对多维向量按指定维度进行逻辑或归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。”明确给出右端事实。Host 查询接口给出 ReduceAny 的临时空间上下界，计算接口明确 sharedTmpBuffer 与归约轴语义，形成空间选择到逻辑或归约的调用链。
<!-- cannbot:related:end -->
