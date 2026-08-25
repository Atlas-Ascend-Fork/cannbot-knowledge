---
type: API
title: GetLogicalOrMaxMinTmpSize
description: 在host侧获取LogicalOr接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOr_interface/GetLogicalOrMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalOrMaxMinTmpSize

host侧Tiling接口，用于获取LogicalOr接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalOrMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [LogicalOr](logical_or.md)（`related`）：LogicalOr 运行前需由 Host 查询最小和最大临时空间，最小值保障正确性并作为 Kernel tiling 参数。
- [GetLogicalOrTmpBufferFactorSize](get_logical_or_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalOrMaxMinTmpSize 与《GetLogicalOrTmpBufferFactorSize》的实质衔接是：GetLogicalOrMaxMinTmpSize 与 factor 查询共同决定 LogicalOr 的 sharedTmpBuffer，接口页和 kernel 操作说明该 tiling 结果的唯一消费方。
- [LogicalOr接口](logical_or_interface.md)（`same_topic`）：GetLogicalOrMaxMinTmpSize 与《LogicalOr接口》的实质衔接是：GetLogicalOrMaxMinTmpSize 与 factor 查询共同决定 LogicalOr 的 sharedTmpBuffer，接口页和 kernel 操作说明该 tiling 结果的唯一消费方。
<!-- cannbot:related:end -->
