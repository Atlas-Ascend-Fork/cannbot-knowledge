---
type: API
title: GetReduceMaxMaxMinTmpSize
description: 在host侧获取ReduceMax接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMax_interface/GetReduceMaxMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceMaxMaxMinTmpSize

host侧Tiling接口，用于获取ReduceMax接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceMaxMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceMax接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [AscReduceMax](../../../c_api/reg/reduce_compute/asc_reduce_max.md)（`same_topic`）：AscReduceMax 与《GetReduceMaxMaxMinTmpSize》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [ReduceMax](reduce_max.md)（`same_topic`）：GetReduceMaxMaxMinTmpSize：该 host 接口专门为 ReduceMax 计算选择 sharedTmpBuffer，ReduceMax 正文中的 isReuseSource/shape 必须与这里的估算入参保持一致。 目标卡《ReduceMax》补充：对多维向量在指定维度求最大值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
- [ReduceMax接口](reduce_max_interface.md)（`same_topic`）：GetReduceMaxMaxMinTmpSize：该 host 接口专门为 ReduceMax 计算选择 sharedTmpBuffer，ReduceMax 正文中的 isReuseSource/shape 必须与这里的估算入参保持一致。 目标卡《ReduceMax接口》补充：对多维向量在指定维度求最大值，并提供临时空间大小获取接口。
<!-- cannbot:related:end -->
