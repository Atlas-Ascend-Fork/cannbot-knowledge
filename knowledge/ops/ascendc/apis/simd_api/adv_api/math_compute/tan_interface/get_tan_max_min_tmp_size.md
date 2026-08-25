---
type: API
title: GetTanMaxMinTmpSize
description: 在host侧获取Tan接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/GetTanMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTanMaxMinTmpSize

host侧Tiling接口，用于获取Tan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetTanMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Tan接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Tan](tan.md)（`related`）：调用 Tan 前据 shape 计算 workspace。
- [GetTanTmpBufferFactorSize](get_tan_tmp_buffer_factor_size.md)（`same_topic`）：GetTanMaxMinTmpSize 与《GetTanTmpBufferFactorSize》的实质衔接是：该 host 查询直接服务 Tan 高阶接口，factor 查询用于把最大最小空间预算转换为实际 tiling 处理量。
- [Tan接口](tan_interface.md)（`same_topic`）：Tan接口 与《GetTanMaxMinTmpSize》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
