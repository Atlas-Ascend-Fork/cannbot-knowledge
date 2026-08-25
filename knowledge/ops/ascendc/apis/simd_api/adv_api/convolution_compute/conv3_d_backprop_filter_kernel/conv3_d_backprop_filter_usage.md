---
type: API
title: Conv3DBackpropFilter使用说明
description: Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Conv3DBackpropFilter_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropFilter使用说明

Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。 卷积反向的权重传播如图1，卷积反向权重计算如图2。 Conv3dBackpropFilter的计算公式为： - X为卷积的特征矩阵Input。 - ∂L/∂Y为卷积正向损失函数对输出Y的梯度GradOutput，作为求反向传播误差∂L/∂W的输入，即卷积的输出反向GradOutput。 - ∂L/∂W为Weight权重的反向传播误差GradWeight。 图1 卷积反向权重传播示意图 图2 卷积反向权重计算过程示意图 Kernel侧实现Conv3DBackpropFilter求解反向传播误差运算的步骤概括为：

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropFilter Tiling侧接口](../conv3_d_backprop_filter_tiling/conv3_d_backprop_filter_tiling.md)（`related`）：Conv3DBackpropFilter Tiling侧接口 与《Conv3DBackpropFilter使用说明》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
- [Conv3DBackpropFilterTiling](../conv3_d_backprop_filter_tiling/conv3_d_backprop_filter_tiling_usage.md)（`related`）：Kernel 使用说明消费 Host GetTiling 生成的结构并给出 Init、Iterate、GetTensorC 顺序，闭合 Host 到 Device 契约。
- [GetTensorC](get_tensor_c.md)（`related`）：Conv3DBackpropFilter使用说明 与《GetTensorC》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [GetTiling](../conv3_d_backprop_filter_tiling/get_tiling.md)（`related`）：GetTiling 与《Conv3DBackpropFilter使用说明》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [SetGradOutput](set_grad_output.md)（`related`）：Conv3DBackpropFilter使用说明 与《SetGradOutput》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [SetStartPosition](set_start_position.md)（`related`）：Conv3DBackpropFilter使用说明 与《SetStartPosition》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [TConv3DBpFilterTiling结构体](../conv3_d_backprop_filter_tiling/t_conv3_d_bp_filter_tiling_struct.md)（`related`）：Conv3DBackpropFilter使用说明 与《TConv3DBpFilterTiling结构体》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel.md)（`same_topic`）：Conv3DBackpropFilter使用说明 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：Iterate（卷积计算） 与《Conv3DBackpropFilter使用说明》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetInput](set_input.md)（`same_topic`）：SetInput 与《Conv3DBackpropFilter使用说明》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《Conv3DBackpropFilter使用说明》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [SetWeightType](../conv3_d_backprop_filter_tiling/set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；Conv3DBackpropFilter使用说明正文界定“Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《Conv3DBackpropFilter使用说明》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [卷积计算Init](init.md)（`same_topic`）：卷积计算Init 与《Conv3DBackpropFilter使用说明》的实质衔接是：Init 消费同一 Conv3DBackpropFilter tiling 并建立资源状态，随后由输入、梯度、起始位置、单 shape、Iterate、取结果和 End 完成一轮对象生命周期。
<!-- cannbot:related:end -->
