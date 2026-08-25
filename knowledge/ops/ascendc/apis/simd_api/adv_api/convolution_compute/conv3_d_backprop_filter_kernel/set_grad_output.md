---
type: API
title: SetGradOutput
description: 设置卷积反向计算的输入矩阵GradOutput。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/SetGradOutput.md
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

- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`related`）：Conv3DBackpropFilter使用说明 与《SetGradOutput》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [SetGradOutput](../conv3_d_backprop_input_kernel/set_grad_output.md)（`related`）：反向输入与反向权重两类卷积都绑定同语义的 GradOutput GM 张量，但服务不同反传目标，可帮助避免混用对象。
- [SetGradOutputType](../conv3_d_backprop_filter_tiling/set_grad_output_type.md)（`related`）：SetGradOutputType 与《SetGradOutput》的实质衔接是：该 setter 把 GradOutput 的 GM/NDC1HWC0 与 FP16/BF16 类型写入 BackpropFilter Host tiling；形状 setter 补齐同一张量描述，GetTiling 生成结构后由 kernel Init/SetGradOutput 按同一契约消费。
- [卷积计算Init](init.md)（`related`）：卷积计算Init 与《SetGradOutput》的实质衔接是：Init 消费同一 Conv3DBackpropFilter tiling 并建立资源状态，随后由输入、梯度、起始位置、单 shape、Iterate、取结果和 End 完成一轮对象生命周期。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：Iterate（卷积计算） 与《SetGradOutput》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetGradOutputShape](../conv3_d_backprop_filter_tiling/set_grad_output_shape.md)（`same_topic`）：Host tiling 先声明 GradOutput 的 NCDHW 形状，Kernel SetGradOutput 才能按同一张量契约解释 GM 地址。
- [SetInput](set_input.md)（`same_topic`）：SetInput 与《SetGradOutput》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《SetGradOutput》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
<!-- cannbot:related:end -->
