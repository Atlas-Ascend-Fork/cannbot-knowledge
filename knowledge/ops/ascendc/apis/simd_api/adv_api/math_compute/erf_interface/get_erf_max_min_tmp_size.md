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

- [Erf](erf.md)（`related`）：“host侧Tiling接口，用于获取Erf接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”与“临时空间大小通过GetErfMaxMinTmpSize获取。”是双方正文中的具体合同。Tiling 卡说明如何取得最大最小临时空间，Erf 计算卡明确把该接口作为 workspace 尺寸来源，二者组成 Host 估算到 Kernel 调用的前置链。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`related`）：“调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。”；“在minValue到maxValue范围内，临时空间越大性能越好。约束：无。”。两张卡提供 Erf 临时空间规划的两种互补合同：factor 路线反推共同 calCount，max/min 路线给出合法容量区间。
<!-- cannbot:related:end -->
