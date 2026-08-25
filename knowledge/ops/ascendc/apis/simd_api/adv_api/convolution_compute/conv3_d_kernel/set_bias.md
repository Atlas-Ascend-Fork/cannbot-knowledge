---
type: API
title: SetBias
description: 设置偏置矩阵Bias。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetBias

设置偏置矩阵Bias。

函数原型：__aicore__ inline void SetBias(const AscendC::GlobalTensor<BiasT>& bias)

参数：
- bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetBiasType](../conv3_d_tiling/set_bias_type.md)（`related`）：Conv3D kernel 的 SetBias 绑定 bias 张量，而 tiling 侧 SetBiasType 声明同一 bias 的 GM 位置、ND 格式和 dtype；两侧配置必须一致。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetBias》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
