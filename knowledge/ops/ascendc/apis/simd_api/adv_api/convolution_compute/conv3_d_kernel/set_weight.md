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

- [IterateAll](iterate_all.md)（`related`）：SetWeight 的动作是“设置权重矩阵Weight。”；IterateAll 规定“IterateAll接口必须在初始化接口及输入输出配置接口之后进行调用”。权重配置属于启动单核 Conv3D 计算前必须完成的输入配置。
<!-- cannbot:related:end -->
