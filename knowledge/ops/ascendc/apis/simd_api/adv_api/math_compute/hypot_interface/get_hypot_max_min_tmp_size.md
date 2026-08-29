---
type: API
title: GetHypotMaxMinTmpSize
description: 在host侧获取Hypot接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Hypot_interface/GetHypotMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetHypotMaxMinTmpSize

host侧Tiling接口，用于获取Hypot接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetHypotMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetHypotTmpBufferFactorSize](get_hypot_tmp_buffer_factor_size.md)（`related`）：获取Hypot接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；host侧Tiling接口，用于获取Hypot接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。一端把 Hypot 临时空间拆为活跃节点倍数与额外缓冲以反推单次元素量，另一端提供最大最小临时空间的 Host Tiling 入口，二者组成 Hypot workspace 预算与计算粒度选择链。
- [Hypot](hypot.md)（`related`）：host侧Tiling接口，用于获取Hypot接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；按元素计算两个浮点数平方和的平方根（dst = sqrt(src0^2 + src1^2)，Hypot(3.0, 4.0)=5.0）。模板参数T支持half/bfloat16_t/float。仅Ascend 950PR/950DT支持。。前者专门计算 Hypot Kernel 所需临时空间的 Tiling 上下界，后者定义实际逐元素平方和开方运算，二者连接 Host 空间预算与 Kernel 调用。
<!-- cannbot:related:end -->
