---
type: API
title: GetLogMaxMinTmpSize
description: Host侧接口，用于获取Log接口能完成计算所需最小的临时空间大小，此空间为预留空间，即需要保证预留有足够的物理空间，用于执行计算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/GetLogMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLogMaxMinTmpSize

host侧Tiling接口，用于获取Log/Log2/Log10接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

提供三个重载：GetLogMaxMinTmpSize、GetLog10MaxMinTmpSize、GetLog2MaxMinTmpSize，函数原型均为：void Get{Log|Log10|Log2}MaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Log接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetLogTmpBufferFactorSize](get_log_tmp_buffer_factor_size.md)（`related`）：host侧Tiling接口，用于获取Log/Log2/Log10接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。。前者从 shape 求临时空间上下界，后者从已定临时空间反推单次元素量，二者闭合 Log tiling 的正反预算。
- [Log](log.md)（`related`）：host侧Tiling接口，用于获取Log/Log2/Log10接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。。Log 计算接口明确以 GetLogMaxMinTmpSize 规划 shared 临时空间，形成 host 预算到 kernel 调用的直接链。
<!-- cannbot:related:end -->
