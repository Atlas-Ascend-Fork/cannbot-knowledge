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

- [Log](log.md)（`related`）：GetLogMaxMinTmpSize 返回的区间正用于为 Log/Log2/Log10 执行分配 sharedTmpBuffer；Log 是其直接消费者。
- [Log接口](log_interface.md)（`related`）：Log 的 sharedTmpBuffer 可由该 Host 查询取得最大/最小边界，再作为 Tiling 依据。
- [GetLogTmpBufferFactorSize](get_log_tmp_buffer_factor_size.md)（`same_topic`）：GetLogTmpBufferFactorSize 与《GetLogMaxMinTmpSize》的实质衔接是：Log 的 factor/max-min 查询服务 Log kernel，log2/log10 和 UB 步长故障补充实现与空间约束。
<!-- cannbot:related:end -->
