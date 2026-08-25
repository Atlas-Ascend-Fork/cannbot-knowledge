---
type: API
title: GetErfMaxMinTmpSize
description: 在host侧获取Erf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/GetErfMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetErfMaxMinTmpSize

host侧Tiling接口，用于获取Erf接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetErfMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource为是否允许修改源操作数；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Erf](erf.md)（`same_topic`）：GetErfMaxMinTmpSize 与《Erf》的衔接是：Erf 临时空间查询以 ErfMaxMinTmpSize 的计算因子和接口约束为依据，查询结果直接决定 Erf 调用可安全使用的 tmpBuffer 大小。
- [Erf接口](erf_interface.md)（`same_topic`）：GetErfMaxMinTmpSize 与《Erf接口》的衔接是：Erf 临时空间查询以 ErfMaxMinTmpSize 的计算因子和接口约束为依据，查询结果直接决定 Erf 调用可安全使用的 tmpBuffer 大小。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`same_topic`）：GetErfMaxMinTmpSize 与《GetErfTmpBufferFactorSize》的衔接是：Erf 临时空间查询以 ErfMaxMinTmpSize 的计算因子和接口约束为依据，查询结果直接决定 Erf 调用可安全使用的 tmpBuffer 大小。
<!-- cannbot:related:end -->
