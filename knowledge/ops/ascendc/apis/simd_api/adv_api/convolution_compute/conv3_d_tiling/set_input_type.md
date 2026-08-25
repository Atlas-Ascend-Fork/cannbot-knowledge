---
type: API
title: SetInputType
description: 设置Input在内存上的位置、数据格式和数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetInputType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputType

设置Input在内存上的位置、数据格式和数据类型。

函数原型：void SetInputType(const ConvCommonApi::TPosition pos, const ConvCommonApi::ConvFormat format, const ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Input在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Input的数据格式。当前仅支持ConvFormat::NDC1HWC0。
- dtype（输入）：Input的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [SetInput](../conv3_d_kernel/set_input.md)（`related`）：tiling 侧 SetInputType 固定 Input 的 GM 位置、NDC1HWC0 格式和 FP16/BF16 dtype，kernel 侧 SetInput 绑定的张量必须满足该合同。
- [SetInputType](../conv3_d_backprop_input_tiling/set_input_type.md)（`related`）：正向 Conv3D 的 InputType 语义相近但对象和 tiling 结构不同；迁移时可对照而不能直接替换。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetInputType》具体提供“设置Input在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
<!-- cannbot:related:end -->
