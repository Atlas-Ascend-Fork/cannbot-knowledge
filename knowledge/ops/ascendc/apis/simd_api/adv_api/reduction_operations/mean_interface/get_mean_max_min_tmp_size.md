---
type: API
title: GetMeanMaxMinTmpSize
description: 在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Mean_interface/GetMeanMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetMeanMaxMinTmpSize

host侧Tiling接口，用于获取Mean接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetMeanMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Mean接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetReduceMeanMaxMinTmpSize](../reduce_mean_interface/get_reduce_mean_max_min_tmp_size.md)（`related`）：Mean 与 ReduceMean 的 Host 临时空间查询签名近似，但对应不同归约接口；并列阅读可避免把 Mean 的 workspace 预算误传给 ReduceMean。
- [GetMeanTmpBufferFactorSize](get_mean_tmp_buffer_factor_size.md)（`same_topic`）：焦点处理Mean 的 workspace factor 推算；GetMeanMaxMinTmpSize正文界定“在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择”。候选是 Mean 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Mean](mean.md)（`same_topic`）：Mean 显式 sharedTmpBuffer 重载要求先由 GetMeanMaxMinTmpSize 根据 shape、dtype 和基本块模式取得空间边界，查询结果直接决定调用能否成立。
- [Mean接口](mean_interface.md)（`same_topic`）：GetMeanMaxMinTmpSize说明在host侧获取Mean接口计算所需最大和最小临时空间大小，供Tiling参数选择；对Mean接口而言，Mean 的末轴二维约束与 ReduceMean 的多维 AR/RA 模式不同；两组 workspace 查询决定各自的 Tiling 空间。
<!-- cannbot:related:end -->
