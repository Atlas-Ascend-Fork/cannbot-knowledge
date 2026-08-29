---
type: API
title: GetLogicalXorMaxMinTmpSize
description: 在host侧获取LogicalXor接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalXor_interface/GetLogicalXorMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalXorMaxMinTmpSize

host侧Tiling接口，用于获取LogicalXor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalXorMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalXorTmpBufferFactorSize](get_logical_xor_tmp_buffer_factor_size.md)（`related`）：Factor 查询卡给出“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize”；MaxMin 查询卡说明“在minValue到maxValue范围内，临时空间越大性能越好。”，两者组成先确定允许空间范围、再由实际 currBuff 反推单次元素数的 Host Tiling 链。
- [LogicalXor](logical_xor.md)（`related`）：计算接口以“count为参与计算元素个数。”消费分块长度；Host 查询接口说明“host侧Tiling接口，用于获取LogicalXor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”，先约束 UB 预算再确定 Kernel 分块。
<!-- cannbot:related:end -->
