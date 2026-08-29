---
type: API
title: GetSignMaxMinTmpSize
description: 在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sign_interface/GetSignMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSignMaxMinTmpSize

host侧Tiling接口，用于获取Sign接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetSignMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Sign接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetSignTmpBufferFactorSize](get_sign_tmp_buffer_factor_size.md)（`related`）：开发者据此选择合适的Tiling参数传入kernel侧；推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize。总量接口确定 Sign 临时空间可选范围，因子接口把实际可用空间反推为单次最大元素数，二者组成 host 到 kernel 的分块 Tiling 计算。
- [Sign](sign.md)（`same_topic`）：临时空间大小通过GetSignMaxMinTmpSize获取；实际预留不能小于该值。Sign 的 sharedTmpBuffer 重载明确依赖 GetSignMaxMinTmpSize，查询接口给出 min/max 和性能取舍，直接决定 kernel 侧临时空间的合法容量。
<!-- cannbot:related:end -->
