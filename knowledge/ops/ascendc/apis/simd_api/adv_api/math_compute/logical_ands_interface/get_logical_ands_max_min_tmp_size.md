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

- [GetLogicalAndsTmpBufferFactorSize](get_logical_ands_tmp_buffer_factor_size.md)（`same_topic`）：max/min 与 factor-size 是 LogicalAnds 同一 workspace 契约的两种查询方式，且多 API 共用空间时都需按最小值规则合并。
- [LogicalAnds](logical_ands.md)（`same_topic`）：LogicalAnds 与《GetLogicalAndsMaxMinTmpSize》的实质衔接是：LogicalAnds 的 scalar 逻辑与接口、两种临时空间查询直接配套；LogicalAnd 是 tensor-tensor 对应形态。
<!-- cannbot:related:end -->
