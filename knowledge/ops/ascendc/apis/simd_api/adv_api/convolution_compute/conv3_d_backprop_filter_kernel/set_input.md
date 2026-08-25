---
type: API
title: SetInput
description: 设置特征矩阵Input。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/SetInput.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInput

设置特征矩阵Input。

函数原型：__aicore__ inline void SetInput(const AscendC::GlobalTensor<SrcT>& input)

参数：
- input（输入）：Input在Global Memory上的首地址。类型为GlobalTensor。特征矩阵Input支持的数据类型SrcT为：half、bfloat16_t。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Iterate（卷积计算）](iterate.md)（`related`）：SetInput 与《Iterate（卷积计算）》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetInputShape](../conv3_d_backprop_filter_tiling/set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《SetInput》说明设置特征矩阵Input。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [SetInputType](../conv3_d_backprop_filter_tiling/set_input_type.md)（`related`）：Host 侧设置的 GM、NDC1HWC0 与 dtype 必须和 Kernel 侧 SetInput 绑定的 GlobalTensor 保持一致。
- [SetSingleShape](set_single_shape.md)（`related`）：SetInput 与《SetSingleShape》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetStartPosition](set_start_position.md)（`related`）：SetInput 与《SetStartPosition》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [卷积计算Init](init.md)（`related`）：SetInput 与《卷积计算Init》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel.md)（`same_topic`）：SetInput 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`same_topic`）：SetInput 与《Conv3DBackpropFilter使用说明》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：SetInput 与《GetTensorC》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetGradOutput](set_grad_output.md)（`same_topic`）：SetInput 与《SetGradOutput》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [卷积计算End](end.md)（`same_topic`）：SetInput 与《卷积计算End》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
<!-- cannbot:related:end -->
