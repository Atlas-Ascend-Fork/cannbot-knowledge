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

- [LogicalXor](logical_xor.md)（`related`）：《LogicalXor》说明按元素进行逻辑异或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。；《GetLogicalXorMaxMinTmpSize》说明在host侧获取LogicalXor接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在LogicalXor执行接口必须与两个workspace查询在Host Tiling和Kernel调用间成套使用上存在可执行的直接衔接。
- [LogicalXor接口](logical_xor_interface.md)（`related`）：Host 侧 max/min 查询决定 LogicalXor Kernel 可用的临时空间。
- [GetLogicalXorTmpBufferFactorSize](get_logical_xor_tmp_buffer_factor_size.md)（`same_topic`）：GetLogicalXorTmpBufferFactorSize 与《GetLogicalXorMaxMinTmpSize》的实质衔接是：factor 查询与 GetLogicalXorMaxMinTmpSize 是同一 LogicalXor 临时空间的两种 Host 侧规划方式，LogicalXor 接口页和算子卡说明该空间由逐元素逻辑异或直接消费。
<!-- cannbot:related:end -->
