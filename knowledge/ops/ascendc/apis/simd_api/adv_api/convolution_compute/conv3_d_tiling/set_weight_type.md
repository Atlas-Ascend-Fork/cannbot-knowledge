---
type: API
title: SetWeightType
description: 设置Weight在内存上的位置、数据格式和数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetWeightType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeightType

设置Weight在内存上的位置、数据格式和数据类型。

函数原型：void SetWeightType(const ConvCommonApi::TPosition pos, const ConvCommonApi::ConvFormat format, const ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Weight在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Weight的数据格式。当前仅支持ConvFormat::FRACTAL_Z_3D。
- dtype（输入）：Weight的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：设置Weight在内存上的位置、数据格式和数据类型；设置Input、Weight、Bias、Output的参数类型信息以及Shape信息；使用说明把 SetWeightType 放入生成 Conv3D 单核 tiling 的完整配置步骤。
<!-- cannbot:related:end -->
