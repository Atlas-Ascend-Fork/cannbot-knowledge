---
type: API
title: GetSinMaxMinTmpSize
description: 在host侧获取Sin接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sin_interface/GetSinMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSinMaxMinTmpSize

host侧Tiling接口，用于获取Sin接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

提供两种重载：一种不带config参数（使用默认SinConfig），另一种带config参数（须与Sin Kernel接口模板参数config保持一致）。函数原型：void GetSinMaxMinTmpSize([const SinConfig& config,] const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Sin接口保持一致，仅float支持开启，half不支持；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetSinTmpBufferFactorSize](get_sin_tmp_buffer_factor_size.md)（`related`）：host侧Tiling接口，用于获取Sin接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧；推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。前者给出 Sin 临时空间的合法选择区间，后者把实际可用空间换算为单次处理元素数，属于同一 Tiling 计算链。
<!-- cannbot:related:end -->
