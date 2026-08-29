---
type: API
title: Conv3DBackpropInput
description: 提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/Conv3DBackpropInput_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropInput

Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。转置卷积Conv3DTranspose与Conv3DBackpropInput具有相同的数学过程，因此用户也可以使用Conv3DBackpropInput高阶API实现转置卷积算子。卷积的正反向传播如图1卷积层的前后向传播示意图，反向传播误差计算如图2 反向传播误差计算示意图。 Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel.md)（`related`）：提供三维卷积反向输入梯度计算的 Kernel 侧接口。；Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。转置卷积Conv3DTranspose与Conv3DBackpropInput具有相同的数学过程，因此用户也可以使用Conv3DBackpropInput高阶API实现转置卷积算子。卷积的正反向传播如图1卷积层的前后向传播示意图，反向传播误差计算如图2 反向传播误差计算示意图。 Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。。Kernel 接口定义计算入口，使用卡明确 GradOutput、转置 Weight 到 GradInput 的调用语义。
- [SetGradOutput](set_grad_output.md)（`related`）：设置卷积反向计算的输入矩阵GradOutput。；Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。。SetGradOutput 卡指定写入卷积反向计算的 GradOutput 输入，使用说明卡给出该输入与转置 Weight 共同计算 GradInput 的数学角色，因此参数设置可直接落到完整反向运算链。
- [卷积计算End](end.md)（`related`）：Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。；在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。。用法卡覆盖 Conv3DBackpropInput 任务，End 卡规定该任务完成后的必需清理步骤。
<!-- cannbot:related:end -->
