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

- [Conv3DUsage](conv3_d_usage.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。。SetBias 的输入合同把 usage 中卷积偏置 B 的 GM 地址和支持 dtype 落到具体配置接口。
- [SetBiasType](../conv3_d_tiling/set_bias_type.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；设置Bias在内存上的位置、数据格式和数据类型。。tiling 侧先声明 Bias 的位置、格式和类型，kernel 侧 SetBias 再接收相应 GM tensor，形成 Host 配置到 Device 入参的合同。
<!-- cannbot:related:end -->
