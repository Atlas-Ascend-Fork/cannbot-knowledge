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

- [GetTensorC](get_tensor_c.md)（`related`）：GetTensorC说明在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵；对Conv3DBackpropInput Kernel侧接口而言，Host 侧生成的 TConv3DBackpropInputTiling 直接喂给 Kernel Init；Kernel 完成 Iterate 后必须用 GetTensorC 将 L0C 结果搬回 GM。
- [GetTiling](../conv3_d_backprop_input_tiling/get_tiling.md)（`related`）：GetTiling 与《Conv3DBackpropInput Kernel侧接口》的衔接是：GetTiling 是 Conv3DBackpropInput 主机侧配置的收口：构造并设置参数后生成 TConv3DBackpropInputTiling，随后由 Kernel 侧按该 tiling 驱动计算。
- [TConv3DBackpropInputTiling结构体](../conv3_d_backprop_input_tiling/t_conv3_d_backprop_input_tiling_struct.md)（`related`）：Kernel 对象消费该结构进行资源划分和迭代，形成 Host/Kernel 直接契约。
- [卷积计算Init](init.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput Kernel侧接口”定义：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput](conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInput Kernel侧接口正文说明“提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [Conv3DBackpropInput Tiling侧接口](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling.md)（`same_topic`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《Conv3DBackpropInput Kernel侧接口》补充：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
- [Conv3DBackpropInputTiling](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：Conv3DBackpropInputTiling说明提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息；对Conv3DBackpropInput Kernel侧接口而言，Host 侧生成的 TConv3DBackpropInputTiling 直接喂给 Kernel Init；Kernel 完成 Iterate 后必须用 GetTensorC 将 L0C 结果搬回 GM。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《Conv3DBackpropInput Kernel侧接口》补充：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
<!-- cannbot:related:end -->
