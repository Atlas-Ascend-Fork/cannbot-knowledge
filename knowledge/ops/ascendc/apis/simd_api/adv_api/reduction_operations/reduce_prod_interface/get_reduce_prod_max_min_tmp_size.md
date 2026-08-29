---
type: API
title: GetReduceProdMaxMinTmpSize
description: 在host侧获取ReduceProd接口计算所需的最大和最小临时空间大小，用于选择合适的空间作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceProd_interface/GetReduceProdMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceProdMaxMinTmpSize

host侧Tiling接口，用于获取ReduceProd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceProdMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceProd接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ReduceProd](reduce_prod.md)（`related`）：host侧Tiling接口，用于获取ReduceProd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceProdMaxMinTmpSize获取。。ReduceProd 正文明确以 GetReduceProdMaxMinTmpSize 计算 sharedTmpBuffer 容量，两卡形成 Host 容量规划到 Kernel 归约调用的直接契约。
<!-- cannbot:related:end -->
