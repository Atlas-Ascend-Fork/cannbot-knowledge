---
type: API
title: GetFracMaxMinTmpSize
description: 在host侧获取Frac接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Frac_interface/GetFracMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetFracMaxMinTmpSize

host侧Tiling接口，用于获取Frac接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetFracMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource为是否允许修改源操作数输入空间；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Frac](frac.md)（`related`）：host侧Tiling接口，用于获取Frac接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetFracMaxMinTmpSize获取。。Host 侧接口产出 Frac 所需临时空间上下界，Frac 计算接口明确以该结果确定 sharedTmpBuffer 容量；这是 Tiling 生产值到 Kernel 调用消费值的直接合同。
- [GetFracTmpBufferFactorSize](get_frac_tmp_buffer_factor_size.md)（`related`）：获取Frac接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；host侧Tiling接口，用于获取Frac接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两接口围绕同一 Frac 临时空间合同工作：前者由既定空间反推单次处理量，后者在 Host Tiling 侧给出可选空间上下界，可连续用于空间预算和 tile 大小求解。
<!-- cannbot:related:end -->
