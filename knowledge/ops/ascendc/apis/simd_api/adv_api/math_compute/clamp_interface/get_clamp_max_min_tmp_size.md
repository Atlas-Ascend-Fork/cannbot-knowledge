---
type: API
title: GetClampMaxMinTmpSize
description: 在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/GetClampMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetClampMaxMinTmpSize

host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetClampMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape信息；typeSize为输入数据类型字节数（half传2）；isReuseSource与ClampMax/ClampMin接口保持一致；maxValue输出最大临时空间大小（超出部分不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间，需开发者自行裁剪）；minValue输出最小临时空间大小（实际预留空间不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大，kernel侧计算性能越好。约束：无。
