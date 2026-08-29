---
type: API
title: Conv3DBackpropInput Tiling侧接口
description: 提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/Conv3DBackpropInput_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropInput Tiling侧接口

提供 Conv3D 反向输入梯度的 Host 侧 Tiling 接口，通过 TConv3DBackpropInputTiling 结构体承载切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetWeightShape/SetInputShape/SetGradOutputShape 设置各张量形状，SetWeightType/SetInputType/SetGradOutputType 设置数据类型。
另提供 SetPadding/SetStride/SetDilation 设置卷积超参数，SetOutputPadding 设置输出填充，适用于反卷积场景。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`related`）：核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。；提供 Conv3D 反向输入梯度的 Host 侧 Tiling 接口，通过 TConv3DBackpropInputTiling 结构体承载切分参数。。Kernel 生命周期消费 GradOutput、Weight、shape 和起始位置，Host Tiling 为该 Kernel 生成切分参数。
<!-- cannbot:related:end -->
