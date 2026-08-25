---
type: API
title: SetWeight
description: 设置卷积反向计算的输入矩阵Weight。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/SetWeight.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeight

设置卷积反向计算的输入矩阵Weight。

函数原型：__aicore__ inline void SetWeight(const AscendC::GlobalTensor<SrcT>& weight)

参数：
- weight（输入）：Weight矩阵在Global Memory上的首地址。类型为GlobalTensor。SrcT表示Weight矩阵的数据类型，当前支持的数据类型为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInputTiling](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling_usage.md)（`related`）：Conv3DBackpropInputTiling说明提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate（卷积计算）说明每次调用Iterate时，会计算出一个baseM \ baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C Buffer中的数据将被写入目标地址。
- [SetSingleWeightShape](../conv3_d_tiling/set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeight》明确提供“设置卷积反向计算的输入矩阵Weight。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetWeight正文说明“设置卷积反向计算的输入矩阵Weight”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetWeightShape](../conv3_d_backprop_input_tiling/set_weight_shape.md)（`same_topic`）：SetWeightShape说明设置权重矩阵Weight的形状。
- [SetWeightType](../conv3_d_backprop_filter_tiling/set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；SetWeight正文界定“设置卷积反向计算的输入矩阵Weight”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
- [SetWeightType](../conv3_d_backprop_input_tiling/set_weight_type.md)（`same_topic`）：SetWeightType说明设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
<!-- cannbot:related:end -->
