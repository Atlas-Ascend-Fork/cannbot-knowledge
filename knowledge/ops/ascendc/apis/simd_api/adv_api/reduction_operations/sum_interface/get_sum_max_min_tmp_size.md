---
type: API
title: GetSumMaxMinTmpSize
description: 在host侧获取Sum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Sum_interface/GetSumMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetSumMaxMinTmpSize

host侧Tiling接口，用于获取Sum接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetSumMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Sum接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Sum](sum.md)（`related`）：Sum 明确要求 sharedTmpBuffer，并把 GetSumMaxMinTmpSize 作为对应 Host sizing 入口；focal 的 max/min 结果直接决定最后一维归约 tile 的合法预算。
- [Sum接口](sum_interface.md)（`same_topic`）：Sum接口 与《GetSumMaxMinTmpSize》的实质衔接是：Sum 沿最后一维求和并由 GetSumMaxMinTmpSize 分配临时空间；ReduceSum 是可指定维度的相关入口，其空间查询与调用边界不同。
<!-- cannbot:related:end -->
