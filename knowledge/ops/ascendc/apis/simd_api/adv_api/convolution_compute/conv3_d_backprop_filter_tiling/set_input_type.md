---
type: API
title: SetInputType
description: 设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetInputType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputType

设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。

函数原型：void SetInputType(ConvCommonApi::TPosition pos, ConvCommonApi::ConvFormat format, ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Input在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Input的数据格式。当前仅支持ConvFormat::NDC1HWC0。
- dtype（输入）：Input的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。
