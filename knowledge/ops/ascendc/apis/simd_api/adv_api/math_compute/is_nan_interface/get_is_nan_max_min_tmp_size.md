---
type: API
title: GetIsNanMaxMinTmpSize
description: 在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsNan_interface/GetIsNanMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetIsNanMaxMinTmpSize

host侧Tiling接口，用于获取IsNan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetIsNanMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetIsNanTmpBufferFactorSize](get_is_nan_tmp_buffer_factor_size.md)（`same_topic`）：《GetIsNanMaxMinTmpSize》处理“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”。《GetIsNanTmpBufferFactorSize》明确提供“获取IsNan接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，其参数、调用或验证步骤直接接入IsNan 的临时空间计算、Kernel 调用和 SIMT 对应实现。
- [IsNan](is_nan.md)（`same_topic`）：《GetIsNanMaxMinTmpSize》处理“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”。《IsNan》明确提供“按元素判断输入浮点数是否为nan，输出浮点数或布尔值”，其参数、调用或验证步骤直接接入IsNan 的临时空间计算、Kernel 调用和 SIMT 对应实现。
- [IsNan接口](is_nan_interface.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《GetIsNanMaxMinTmpSize》提供“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
<!-- cannbot:related:end -->
