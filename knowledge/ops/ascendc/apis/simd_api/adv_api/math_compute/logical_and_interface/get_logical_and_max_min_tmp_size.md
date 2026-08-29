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

- [GetLogicalAndTmpBufferFactorSize](get_logical_and_tmp_buffer_factor_size.md)（`related`）：获取LogicalAnd接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；host侧Tiling接口，用于获取LogicalAnd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两个 Host 侧接口共同完成 LogicalAnd 的临时空间规划：一个反推单次 shape，另一个给出可分配空间上下界。
- [LogicalAnd](logical_and.md)（`related`）：host侧Tiling接口，用于获取LogicalAnd接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；按元素进行逻辑与操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。。Host 侧 tmp-size 查询为 kernel 侧 LogicalAnd 分配临时空间并选择 tiling 参数，直接支撑该逐元素逻辑与调用。
<!-- cannbot:related:end -->
