---
type: API
title: GetLogicalNotMaxMinTmpSize
description: 在host侧获取LogicalNot接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalNot_interface/GetLogicalNotMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalNotMaxMinTmpSize

host侧Tiling接口，用于获取LogicalNot接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalNotMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalNotTmpBufferFactorSize](get_logical_not_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalNotTmpBufferFactorSize 与《GetLogicalNotMaxMinTmpSize》的实质衔接是：LogicalNot 的临时空间 factor 查询需结合 MaxMin 同类空间协议和 LogicalNot 实际调用，才能把查询结果用于 kernel 初始化。
- [LogicalNot](logical_not.md)（`same_topic`）：LogicalNot 与《GetLogicalNotMaxMinTmpSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
<!-- cannbot:related:end -->
