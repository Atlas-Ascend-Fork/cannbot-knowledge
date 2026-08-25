---
type: API
title: 卷积计算End
description: 在Conv3DBackpropFilter卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 卷积计算End

在Conv3DBackpropFilter卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。

函数原型：__aicore__ inline void End()

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel.md)（`same_topic`）：卷积计算End 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [Conv3DBackpropFilter使用说明](conv3_d_backprop_filter_usage.md)（`same_topic`）：卷积计算End 与《Conv3DBackpropFilter使用说明》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：卷积计算End 与《GetTensorC》的实质衔接是：End 是 Conv3DBackpropFilter 对象在 Init、配置输入、Iterate 与 GetTensorC 之后的强制收尾，负责清理 EventID 和内部临时资源。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：Iterate（卷积计算） 与《卷积计算End》的实质衔接是：该 Iterate 必须在 BackpropFilter Init、输入/梯度、SingleShape 与起始位置配置后循环执行，每轮结果由 GetTensorC 搬出，最终 End 清理对象。
- [SetInput](set_input.md)（`same_topic`）：SetInput 与《卷积计算End》的实质衔接是：SetInput 把 Conv3DBackpropFilter 的 GM 特征矩阵绑定到已 Init 的对象，随后与 grad-output、shape/position、Iterate、取结果和 End 组成同一执行生命周期。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape 与《卷积计算End》的实质衔接是：SetSingleShape 在运行时改变 BackpropFilter 单核 M/N/K，必须与 Init、输入/梯度、起始位置、Iterate/GetTensorC 和 End 的同一对象生命周期一致。
- [卷积计算End](../conv3_d_kernel/end.md)（`same_topic`）：卷积计算End 与《卷积计算End》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：卷积计算Init 与《卷积计算End》的实质衔接是：Init 消费同一 Conv3DBackpropFilter tiling 并建立资源状态，随后由输入、梯度、起始位置、单 shape、Iterate、取结果和 End 完成一轮对象生命周期。
<!-- cannbot:related:end -->
