---
type: API
title: GetReduceMeanMaxMinTmpSize
description: 在host侧获取ReduceMean接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMean_interface/GetReduceMeanMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceMeanMaxMinTmpSize

host侧Tiling接口，用于获取ReduceMean接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceMeanMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceMean接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetMeanMaxMinTmpSize](../mean_interface/get_mean_max_min_tmp_size.md)（`related`）：Mean 与 ReduceMean 的 Host 临时空间查询签名近似，但对应不同归约接口；并列阅读可避免把 Mean 的 workspace 预算误传给 ReduceMean。
- [ReduceMean](reduce_mean.md)（`same_topic`）：GetReduceMeanMaxMinTmpSize：该 host估算的shape/typeSize/isReuseSource必须与 ReduceMean kernel调用一致；ReduceMean接口页汇总同一 sharedTmpBuffer契约。 目标卡《ReduceMean》补充：对多维向量按指定维度求平均值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
- [ReduceMean接口](reduce_mean_interface.md)（`same_topic`）：GetReduceMeanMaxMinTmpSize：该 host估算的shape/typeSize/isReuseSource必须与 ReduceMean kernel调用一致；ReduceMean接口页汇总同一 sharedTmpBuffer契约。 目标卡《ReduceMean接口》补充：对多维向量在指定维度求平均值，并提供临时空间大小获取接口。
<!-- cannbot:related:end -->
