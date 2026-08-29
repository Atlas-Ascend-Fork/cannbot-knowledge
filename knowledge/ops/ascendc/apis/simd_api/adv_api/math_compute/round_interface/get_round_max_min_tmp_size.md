---
type: API
title: GetRoundMaxMinTmpSize
description: 在host侧获取Round接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/GetRoundMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetRoundMaxMinTmpSize

host侧Tiling接口，用于获取Round接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetRoundMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Round接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Round](round.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRoundMaxMinTmpSize获取。；host侧Tiling接口，用于获取Round接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；目标产生 Round 所需 workspace 上下界，焦点消费该 Tiling 结果配置临时空间。
- [GetRoundTmpBufferFactorSize](get_round_tmp_buffer_factor_size.md)（`same_topic`）：host侧Tiling接口，用于获取Round接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。 获取Round接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。 一个从 shape 求空间区间，一个从固定空间预算反推处理规模，是 Round Host Tiling 的两种互补容量计算。
<!-- cannbot:related:end -->
