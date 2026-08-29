---
type: API
title: SetBiasType
description: 设置Bias在内存上的位置、数据格式和数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetBiasType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetBiasType

设置Bias在内存上的位置、数据格式和数据类型。

函数原型：void SetBiasType(const ConvCommonApi::TPosition pos, const ConvCommonApi::ConvFormat format, const ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Bias在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Bias的数据格式。当前仅支持ConvFormat::ND。
- dtype（输入）：Bias的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::FLOAT。

<!-- cannbot:related:start -->
## 相关

- [SetBias](../conv3_d_kernel/set_bias.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；设置Bias在内存上的位置、数据格式和数据类型。。tiling 侧先声明 Bias 的位置、格式和类型，kernel 侧 SetBias 再接收相应 GM tensor，形成 Host 配置到 Device 入参的合同。
<!-- cannbot:related:end -->
