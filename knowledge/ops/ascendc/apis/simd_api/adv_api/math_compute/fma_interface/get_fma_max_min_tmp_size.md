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

- [Fma](fma.md)（`related`）：GetFmaMaxMinTmpSize 给出的上下界用于 Fma 的 sharedTmpBuffer；低于最小值会破坏正确性，区间内增加空间可改善性能。
- [Fma接口](fma_interface.md)（`same_topic`）：Fma接口 与《GetFmaMaxMinTmpSize》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [GetFmaTmpBufferFactorSize](get_fma_tmp_buffer_factor_size.md)（`same_topic`）：MaxMin 接口按 shape 正向求 Fma 空间上下界，FactorSize 接口按既有空间反推可处理规模，两者是同一临时空间模型的正反查询。
<!-- cannbot:related:end -->
