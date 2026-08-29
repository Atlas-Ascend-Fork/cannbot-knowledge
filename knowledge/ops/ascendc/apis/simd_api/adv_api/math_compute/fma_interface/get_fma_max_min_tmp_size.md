---
type: API
title: GetFmaMaxMinTmpSize
description: 在host侧获取Fma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fma_interface/GetFmaMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetFmaMaxMinTmpSize

host侧Tiling接口，用于获取Fma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetFmaMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Fma](fma.md)（`related`）：host侧Tiling接口，用于获取Fma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。接口内部涉及精度转换，临时空间大小通过GetFmaMaxMinTmpSize获取。。Host 查询提供 Fma 缓冲上下界，Kernel 执行重载消费显式或框架申请的临时空间，闭合 Tiling 到执行链。
- [GetFmaTmpBufferFactorSize](get_fma_tmp_buffer_factor_size.md)（`related`）：获取Fma接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；host侧Tiling接口，用于获取Fma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。一张卡给出固定空间的 factor/extraBuf 换算，另一张给出最大最小缓冲查询，二者共同完成 Host Tiling 容量选择。
<!-- cannbot:related:end -->
