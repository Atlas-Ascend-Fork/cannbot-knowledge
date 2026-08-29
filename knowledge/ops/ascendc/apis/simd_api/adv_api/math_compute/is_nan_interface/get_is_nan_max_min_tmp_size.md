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

- [GetIsNanTmpBufferFactorSize](get_is_nan_tmp_buffer_factor_size.md)（`related`）：获取IsNan接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；host侧Tiling接口，用于获取IsNan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两接口分别从固定临时空间反推单次元素量、按输入 shape 求临时空间上下界，共同完成 IsNan 的 Host Tiling 容量决策。
- [IsNan](is_nan.md)（`related`）：host侧Tiling接口，用于获取IsNan接口所需的最大和最小临时空间大小；临时空间大小通过GetIsNanMaxMinTmpSize获取。。左卡返回 IsNan 可用临时空间范围，右卡明确由该查询结果为 sharedTmpBuffer 定容；两端直接衔接 950 Host Tiling 与按元素 NaN 判定 Kernel。
<!-- cannbot:related:end -->
