---
type: API
title: GetLogicalAndsMaxMinTmpSize
description: 在host侧获取LogicalAnds接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalAnds_interface/GetLogicalAndsMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalAndsMaxMinTmpSize

host侧Tiling接口，用于获取LogicalAnds接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalAndsMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalAndsTmpBufferFactorSize](get_logical_ands_tmp_buffer_factor_size.md)（`related`）：获取LogicalAnds接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；host侧Tiling接口，用于获取LogicalAnds接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；factor 接口按固定临时空间反推单次元素数，max/min 接口给出可选临时空间区间，二者共同闭合 Host Tiling 容量计算。
- [LogicalAnds](logical_ands.md)（`related`）：输入矢量每个元素与标量进行逻辑与操作。当数据类型不是bool时，零视为False，非零视为True。；host侧Tiling接口，用于获取LogicalAnds接口所需的最大和最小临时空间大小。前者定义 Kernel 计算，后者给出为该接口准备临时空间的 Host Tiling 契约。
<!-- cannbot:related:end -->
