---
type: API
title: GetLogicalOrsMaxMinTmpSize
description: 在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOrs_interface/GetLogicalOrsMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetLogicalOrsMaxMinTmpSize

host侧Tiling接口，用于获取LogicalOrs接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetLogicalOrsMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetLogicalOrsTmpBufferFactorSize](get_logical_ors_tmp_buffer_factor_size.md)（`related`）：焦点接口给出“在minValue到maxValue范围内，临时空间越大性能越好。”的分配区间；目标接口给出“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize”，可在固定 UB 预算下反推单次 shape，两者是 LogicalOrs Host Tiling 的正向预算与反向求块配套合同。
- [LogicalOrs](logical_ors.md)（`related`）：输入矢量每个元素与标量进行逻辑或操作。；host侧Tiling接口，用于获取LogicalOrs接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。计算接口定义 LogicalOrs 的逐元素逻辑或语义，该 Host Tiling 接口提供执行它所需的临时空间上下界。
<!-- cannbot:related:end -->
