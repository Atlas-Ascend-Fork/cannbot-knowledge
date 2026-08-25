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

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：SetWeightType 是 Conv3D Host tiling 初始化流程中的必需类型配置；使用说明明确它需与 Input/Bias/Output 类型及形状、stride/padding 等一起在 GetTiling 前设置。
- [SetOrgWeightShape](set_org_weight_shape.md)（`related`）：权重类型与原始 Co/Kd/Kh/Kw 形状共同构成 Conv3D tiling 对 Weight 的完整描述，缺一不能可靠生成切分参数。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetWeightType》具体提供“设置Weight在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetWeight](../conv3_d_kernel/set_weight.md)（`related`）：Host SetWeightType 固定 Weight 为 GM/FRACTAL_Z_3D/FLOAT16 或 BF16，必须与 Kernel SetWeight 绑定的 GlobalTensor 类型和布局一致。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetWeightType》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetSingleWeightShape](set_single_weight_shape.md)（`same_topic`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeightType》明确提供“设置Weight在内存上的位置、数据格式和数据类型。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](../conv3_d_backprop_filter_tiling/set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；SetWeightType正文界定“设置Weight在内存上的位置、数据格式和数据类型”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
<!-- cannbot:related:end -->
