---
type: API
title: GetXorMaxMinTmpSize
description: 在host侧获取Xor接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Xor_interface/GetXorMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetXorMaxMinTmpSize

host侧Tiling接口，用于获取Xor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetXorMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Xor接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Xor](xor.md)（`related`）：提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetXorMaxMinTmpSize获取。；host侧Tiling接口，用于获取Xor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Xor 计算接口消费临时空间，Host Tiling 查询接口给出可传给 Kernel 的上下界，两者构成同一临时空间配置链。
- [GetXorTmpBufferFactorSize](get_xor_tmp_buffer_factor_size.md)（`same_topic`）：host侧Tiling接口，用于获取Xor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。获取Xor接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。两端共同定义 Xor 临时空间规划的两个方向：先由 shape 确定可选空间范围，或由既定空间反推单次处理量，Host 可据此检查 Tiling 是否自洽。
<!-- cannbot:related:end -->
