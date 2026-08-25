---
type: API
title: SetWeightShape
description: 设置权重矩阵Weight的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeightShape

设置权重矩阵Weight的形状。

参数：
- cout（输入）：设置卷积正向的输出channel大小，与GradOutput的Channel大小一致。
- cin（输入）：设置卷积正向的输入channel大小，与GradInput的Channel大小一致。
- d：输入设置weight的Depth值。
- h：输入设置weight的Height值。
- w：输入设置weight的Width值。

返回值：true表示设置成功，false表示设置失败。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling.md)（`related`）：SetWeightShape 与《Conv3DBackpropInput Tiling侧接口》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [Conv3DBackpropInput Tiling构造函数](conv3_d_backprop_input_tiling_constructor.md)（`related`）：SetWeightShape 与《Conv3DBackpropInput Tiling构造函数》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`related`）：SetWeightShape 与《Conv3DBackpropInputTiling》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [GetTiling](get_tiling.md)（`related`）：SetWeightShape 与《GetTiling》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetDilation](set_dilation.md)（`related`）：SetDilation 的三个扩张量直接作用于 Weight 的 D/H/W 核尺寸；SetWeightShape 提供这三个原始尺寸，二者共同决定反向输入卷积的有效核范围。
- [SetGradOutputShape](set_grad_output_shape.md)（`related`）：SetWeightShape 与《SetGradOutputShape》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetInputShape](set_input_shape.md)（`related`）：SetWeightShape 与《SetInputShape》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetWeightShape](../conv3_d_backprop_filter_tiling/set_weight_shape.md)（`related`）：Conv3DBackpropInput 与 BackpropFilter 都暴露同名 SetWeightShape，但前者用 cout/zin 与 GradInput 对齐，后者服务 GradWeight 切分；并列阅读能避免在两套 Tiling 类之间误套参数语义。
- [SetWeightType](set_weight_type.md)（`related`）：SetWeightShape 与《SetWeightType》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`related`）：SetWeightShape 与《TConv3DBackpropInputTiling结构体》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetWeight](../conv3_d_backprop_input_kernel/set_weight.md)（`same_topic`）：SetWeightShape说明设置权重矩阵Weight的形状。
<!-- cannbot:related:end -->
