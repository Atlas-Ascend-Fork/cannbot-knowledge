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

- [LogicalOrs](logical_ors.md)（`related`）：《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递；《LogicalOrs》说明输入矢量每个元素与标量进行或操作，非零视为真。二者在LogicalOrs的Host侧最大/最小临时空间与factor查询共同为同一个Kernel接口确定workspace预算上存在可执行的直接衔接。
- [GetLogicalOrsTmpBufferFactorSize](get_logical_ors_tmp_buffer_factor_size.md)（`same_topic`）：《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递；《GetLogicalOrsTmpBufferFactorSize》说明获取LogicalOrs接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。二者在LogicalOrs的Host侧最大/最小临时空间与factor查询共同为同一个Kernel接口确定workspace预算上存在可执行的直接衔接。
- [LogicalOrs接口](logical_ors_interface.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
