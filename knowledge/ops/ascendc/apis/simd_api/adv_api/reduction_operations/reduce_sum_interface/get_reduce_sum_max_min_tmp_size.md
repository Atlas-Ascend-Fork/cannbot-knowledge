---
type: API
title: GetReduceSumMaxMinTmpSize
description: 在host侧获取ReduceSum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/GetReduceSumMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceSumMaxMinTmpSize

host侧Tiling接口，用于获取ReduceSum接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceSumMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceSum接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ReduceSum](reduce_sum.md)（`related`）：host侧Tiling接口，用于获取ReduceSum接口所需的最大和最小临时空间大小；临时空间大小通过GetReduceSumMaxMinTmpSize获取。。左卡按 ReduceSum 的 shape、dtype 与复用配置返回缓冲范围，右卡明确使用该结果为 sharedTmpBuffer 定容；两端衔接 Host 空间规划与 AR/RA 归约执行。
<!-- cannbot:related:end -->
