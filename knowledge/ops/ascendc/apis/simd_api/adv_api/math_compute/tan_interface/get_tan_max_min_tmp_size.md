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

- [Tan](tan.md)（`related`）：提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanMaxMinTmpSize获取。；host侧Tiling接口，用于获取Tan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Kernel 侧重载明确把临时空间容量交给 GetTanMaxMinTmpSize，Host 侧查询再把容量作为 Tiling 参数回传，闭合 Tan 的分块与 buffer 规划。
- [Tan接口](tan_interface.md)（`same_topic`）：临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。；host侧Tiling接口，用于获取Tan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。前者声明 Tan 的临时空间获取方式，后者给出对应 Host 查询入口，两者闭合 sharedTmpBuffer 的准备步骤。
<!-- cannbot:related:end -->
