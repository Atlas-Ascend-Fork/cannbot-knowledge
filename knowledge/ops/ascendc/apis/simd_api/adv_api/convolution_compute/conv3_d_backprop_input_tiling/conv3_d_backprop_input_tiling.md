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

- [Conv3DBackpropInput](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_usage.md)（`related`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInput Tiling侧接口正文说明“提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [GetTiling](get_tiling.md)（`related`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《GetTiling》补充：获取Tiling参数。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《Conv3DBackpropInput Tiling侧接口》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [卷积计算Init](../conv3_d_backprop_input_kernel/init.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput Tiling侧接口”定义：提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`same_topic`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《Conv3DBackpropInput Kernel侧接口》补充：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《Conv3DBackpropInputTiling》补充：提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`same_topic`）：tiling 总页定义该结构保存的规格字段和 Host 配置入口。
<!-- cannbot:related:end -->
