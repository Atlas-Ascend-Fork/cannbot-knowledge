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

- [ReduceMax](reduce_max.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMaxMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。；host侧Tiling接口，用于获取ReduceMax接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ReduceMax 明确要求以 GetReduceMaxMaxMinTmpSize 决定临时空间，目标卡则定义该 Host 查询的上下界输出，二者构成 Host Tiling 到 Kernel 归约调用的资源配置链。
<!-- cannbot:related:end -->
