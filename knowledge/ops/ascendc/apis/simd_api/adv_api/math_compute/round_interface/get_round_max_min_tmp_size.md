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

- [Lroundf](../../../../simt_api/math_functions/float_math_functions/lroundf.md)（`related`）：Lroundf 与《GetRoundMaxMinTmpSize》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [GetRoundTmpBufferFactorSize](get_round_tmp_buffer_factor_size.md)（`same_topic`）：GetRoundMaxMinTmpSize说明在host侧获取Round接口预留或申请临时空间的最大和最小值，用于Tiling参数传递。
- [Round](round.md)（`same_topic`）：Round 的临时空间需在 Host 侧用 GetRoundMaxMinTmpSize 计算并随 tiling 传入。
<!-- cannbot:related:end -->
