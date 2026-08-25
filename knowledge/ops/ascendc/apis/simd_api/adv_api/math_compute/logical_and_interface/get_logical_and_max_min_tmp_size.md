---
type: API
title: GetLogicalAndMaxMinTmpSize
description: 在host侧获取LogicalAnd接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalAnd_interface/GetLogicalAndMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetLogicalAndMaxMinTmpSize

host侧Tiling接口，用于获取LogicalAnd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalAndMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [LogicalAnd](logical_and.md)（`related`）：LogicalAnd 不允许输入输出地址重叠并需要临时空间；该 host 接口给出可正确执行所需的最小/最大 workspace。
- [GetLogicalAndTmpBufferFactorSize](get_logical_and_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalAndMaxMinTmpSize 与《GetLogicalAndTmpBufferFactorSize》的实质衔接是：LogicalAnd 的 MaxMin 查询须与 factor 查询及 kernel 接口配套，才能确定临时空间与实际调用。
<!-- cannbot:related:end -->
