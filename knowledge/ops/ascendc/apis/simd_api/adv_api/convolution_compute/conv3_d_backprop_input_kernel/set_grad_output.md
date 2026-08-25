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

- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate（卷积计算）说明每次调用Iterate时，会计算出一个baseM \ baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合使用；在调用本接口后，再调用GetTensorC接口，L0C Buffer中的数据将被写入目标地址。
- [SetGradOutput](../conv3_d_backprop_filter_kernel/set_grad_output.md)（`related`）：反向输入与反向权重两类卷积都绑定同语义的 GradOutput GM 张量，但服务不同反传目标，可帮助避免混用对象。
- [SetGradOutputShape](../conv3_d_backprop_input_tiling/set_grad_output_shape.md)（`related`）：Host 侧设置的 GradOutput 形状必须与 Kernel 侧绑定的实际 GradOutput 张量一致，连接 tiling 配置和计算输入。
- [SetStartPosition](set_start_position.md)（`related`）：SetStartPosition 定位的正是 GradOutput 在 D/H 方向的载入起点，必须与 SetGradOutput 绑定的 GM 张量共同解释地址。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetGradOutput正文说明“设置卷积反向计算的输入矩阵GradOutput”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetGradOutputType](../conv3_d_backprop_input_tiling/set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《SetGradOutput》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
<!-- cannbot:related:end -->
