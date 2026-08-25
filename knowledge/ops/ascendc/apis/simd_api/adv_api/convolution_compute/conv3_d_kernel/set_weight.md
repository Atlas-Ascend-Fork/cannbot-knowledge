---
type: API
title: SetWeight
description: 设置权重矩阵Weight。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetWeight.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeight

设置权重矩阵Weight。

函数原型：__aicore__ inline void SetWeight(const AscendC::GlobalTensor<WeightT>& weight)

参数：
- weight（输入）：Weight在Global Memory上的地址。类型为GlobalTensor。权重矩阵Weight支持的数据类型为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [IterateAll](iterate_all.md)（`related`）：SetWeight 与其他输入输出配置完成后才能调用 IterateAll；后者消费已绑定权重完成单核 singleCo×singleDo×singleM 计算。
- [SetSingleWeightShape](../conv3_d_tiling/set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeight》明确提供“设置权重矩阵Weight。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](../conv3_d_tiling/set_weight_type.md)（`related`）：Host SetWeightType 固定 Weight 为 GM/FRACTAL_Z_3D/FLOAT16 或 BF16，必须与 Kernel SetWeight 绑定的 GlobalTensor 类型和布局一致。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetWeight》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
