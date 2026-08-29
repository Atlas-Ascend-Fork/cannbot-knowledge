---
type: API
title: Conv3DBackpropInput Kernel侧接口
description: 提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/Conv3DBackpropInput_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropInput Kernel侧接口

提供三维卷积反向输入梯度计算的 Kernel 侧接口。
核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。
与前向 Conv3D Kernel 接口相比，输入侧改为接收梯度输出与权重，输出为输入梯度。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`related`）：提供三维卷积反向输入梯度计算的 Kernel 侧接口。；Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。转置卷积Conv3DTranspose与Conv3DBackpropInput具有相同的数学过程，因此用户也可以使用Conv3DBackpropInput高阶API实现转置卷积算子。卷积的正反向传播如图1卷积层的前后向传播示意图，反向传播误差计算如图2 反向传播误差计算示意图。 Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。。Kernel 接口定义计算入口，使用卡明确 GradOutput、转置 Weight 到 GradInput 的调用语义。
- [Conv3DBackpropInput Tiling侧接口](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling.md)（`related`）：核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。；提供 Conv3D 反向输入梯度的 Host 侧 Tiling 接口，通过 TConv3DBackpropInputTiling 结构体承载切分参数。。Kernel 生命周期消费 GradOutput、Weight、shape 和起始位置，Host Tiling 为该 Kernel 生成切分参数。
- [TConv3DBackpropInputTiling结构体](../conv3_d_backprop_input_tiling/t_conv3_d_backprop_input_tiling_struct.md)（`related`）：核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。；TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。。结构体卡明确参数被传给 Kernel，Kernel 卡给出消费这些参数的初始化与迭代生命周期。
<!-- cannbot:related:end -->
