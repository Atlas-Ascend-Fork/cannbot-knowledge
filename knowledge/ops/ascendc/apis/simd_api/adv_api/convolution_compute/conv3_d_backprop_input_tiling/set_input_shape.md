---
type: API
title: SetInputShape
description: 设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。在构建Conv3DTranspose算子时，此接口无实际意义，请勿使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetInputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputShape

设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。在构建Conv3DTranspose算子时，此接口无实际意义，请勿使用。

参数：
- n：输入输入Input的Batch值。
- c：输入输入Input的Channel值。
- d：输入输入Input的Depth值。
- h：输入输入Input的Height值。
- w：输入输入Input的Width值。

返回值：true表示设置成功，false表示设置失败。

<!-- cannbot:related:start -->
## 相关

- [SetGradOutputShape](set_grad_output_shape.md)（`related`）：SetInputShape 给出待求梯度 Input 的 N/C/D/H/W，SetGradOutputShape 给出反向输入卷积的上游梯度几何；两者的 batch/channel 对应关系和空间尺寸共同约束 tiling。
- [SetInputShape](../conv3_d_backprop_filter_tiling/set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。在构建Conv3DTranspose算子时，此接口无实际意义，请勿使用。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [SetInputType](set_input_type.md)（`related`）：SetInputShape 提供几何维度，SetInputType 提供存储与 dtype，两者共同构成完整 Input 描述。
- [SetOutputPadding](set_output_padding.md)（`related`）：SetOutputPadding 与《SetInputShape》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《SetInputShape》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
<!-- cannbot:related:end -->
