---
type: API
title: Conv3DBackpropInput Tiling构造函数
description: 用于创建一个Conv3DBackpropInput单核Tiling对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/Conv3DBackpropInput_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropInput Tiling构造函数

用于创建一个Conv3DBackpropInput单核Tiling对象。

参数：
- ascendcPlatform（输入）：传入硬件平台的信息，PlatformAscendC定义请参见构造及析构函数。
- platform（输入）：传入硬件版本以及AI Core中各个硬件单元提供的内存大小。PlatformInfo构造时通过构造及析构函数获取。 PlatformInfo结构定义如下代码所示，socVersion通过GetSocVersion获取并透传，各类硬件存储空间大小通过GetCoreMemSize获取并透传。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：构造函数创建单核 tiling 对象；配置 shape/type/stride 后必须调用 GetTiling 才生成传给 Kernel 的结构体。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《Conv3DBackpropInput Tiling构造函数》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`related`）：构造对象的最终产物写入 TConv3DBackpropInputTiling，Kernel 侧依赖该结构中的切分参数。
<!-- cannbot:related:end -->
