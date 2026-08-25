---
type: API
title: 卷积计算Init
description: Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput
  Tiling侧接口。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# 卷积计算Init

Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。

函数原型：__aicore__ inline void Init(const TConv3DBackpropInputTiling* __restrict tiling)

参数：
- tiling（输入）：Conv3DBackpropInput对象的Tiling参数，TConv3DBackpropInputTiling结构体的定义请参见TConv3DBackpropInputTiling结构体。。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput”定义：提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput Kernel侧接口”定义：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput Tiling侧接口](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput Tiling侧接口”定义：提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Iterate（卷积计算）](iterate.md)（`related`）：Iterate 必须在 Init 及输入输出配置之后调用。
- [SetOutputPadding](../conv3_d_backprop_input_tiling/set_output_padding.md)（`related`）：SetOutputPadding 与《卷积计算Init》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetSingleShape](set_single_shape.md)（`related`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《卷积计算Init》补充：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。
- [TConv3DBackpropInputTiling结构体](../conv3_d_backprop_input_tiling/t_conv3_d_backprop_input_tiling_struct.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“TConv3DBackpropInputTiling结构体”定义：TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInputTiling](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：卷积计算Init说明Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。
- [SetGradOutputType](../conv3_d_backprop_input_tiling/set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《卷积计算Init》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [卷积计算End](end.md)（`same_topic`）：Init 建立 Conv3DBackpropInput 内部状态，End 必须在计算后清理同一对象的 EventID 和临时内存。
<!-- cannbot:related:end -->
