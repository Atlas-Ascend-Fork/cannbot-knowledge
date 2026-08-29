---
type: API
title: SetGradOutput
description: 设置卷积反向计算的输入矩阵GradOutput。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/SetGradOutput.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGradOutput

设置卷积反向计算的输入矩阵GradOutput。

函数原型：__aicore__ inline void SetGradOutput(const AscendC::GlobalTensor<SrcT>& gradOutput)

参数：
- gradOutput（输入）：GradOutput矩阵在Global Memory上的首地址。类型为GlobalTensor。SrcT表示GradOutput矩阵的数据类型，当前支持的数据类型为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`related`）：设置卷积反向计算的输入矩阵GradOutput。；Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。。SetGradOutput 卡指定写入卷积反向计算的 GradOutput 输入，使用说明卡给出该输入与转置 Weight 共同计算 GradInput 的数学角色，因此参数设置可直接落到完整反向运算链。
<!-- cannbot:related:end -->
