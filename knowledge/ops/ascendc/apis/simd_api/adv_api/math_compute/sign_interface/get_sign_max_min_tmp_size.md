---
type: API
title: GetSignMaxMinTmpSize
description: 在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sign_interface/GetSignMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSignMaxMinTmpSize

host侧Tiling接口，用于获取Sign接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetSignMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Sign接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetSignTmpBufferFactorSize](get_sign_tmp_buffer_factor_size.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《GetSignMaxMinTmpSize》补充：在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
- [Sign](sign.md)（`same_topic`）：Sign 计算的 sharedTmpBuffer 由该 Host 接口按 shape 查询并写入 Tiling。
- [Sign接口](sign_interface.md)（`same_topic`）：GetSignMaxMinTmpSize说明在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
<!-- cannbot:related:end -->
