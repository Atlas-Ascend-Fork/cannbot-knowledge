---
type: API
title: SetOutputPadding
description: 构建Conv3DTranspose算子时，设置输出的Padding大小，用于推导输出的形状。在构建Conv3DBackpropInput算子时，此接口无实际意义，请勿使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetOutputPadding.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# SetOutputPadding

构建Conv3DTranspose算子时，设置输出的Padding大小，用于推导输出的形状。在构建Conv3DBackpropInput算子时，此接口无实际意义，请勿使用。

参数：
- outputPadD（输入）：输出在Depth方向的Padding值。
- outputPadH（输入）：输出在Height方向的Padding值。
- outputPadW（输入）：输出在Width方向的Padding值。

返回值：true表示设置成功，false表示设置失败。

<!-- cannbot:related:start -->
## 相关

- [fusion pass SetAttr output_padding 非根因](../../../../../runbooks/compilation/fusion_pass_setattr_output_padding.md)（`exemplifies`）：SetOutputPadding 与《fusion pass SetAttr output_padding 非根因》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [Conv3DBackpropInput](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_usage.md)（`related`）：SetOutputPadding 与《Conv3DBackpropInput》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`related`）：SetOutputPadding 与《Conv3DBackpropInputTiling》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [GetTiling](get_tiling.md)（`related`）：SetOutputPadding 与《GetTiling》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetInputShape](set_input_shape.md)（`related`）：SetOutputPadding 与《SetInputShape》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetPadding](set_padding.md)（`related`）：SetOutputPadding 与《SetPadding》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetStride](set_stride.md)（`related`）：Conv3DTranspose 下 output padding 用于消除 stride 引起的输出尺寸歧义，不能独立设置。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`related`）：SetOutputPadding 与《TConv3DBackpropInputTiling结构体》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [卷积计算Init](../conv3_d_backprop_input_kernel/init.md)（`related`）：SetOutputPadding 与《卷积计算Init》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
<!-- cannbot:related:end -->
