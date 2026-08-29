---
type: API
title: Conv3D模板参数
description: 创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。
  - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3D_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D模板参数

创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。

函数原型：template <class INPUT_TYPE, class WEIGHT_TYPE, class OUTPUT_TYPE, class BIAS_TYPE = biasType, class CONV_CFG = Conv3dParam>

参数：
- INPUT_TYPE（输入）：ConvType类型模板参数，指定Input的参数类型信息。
- WEIGHT_TYPE（输入）：ConvType类型模板参数，指定Weight的参数类型信息。
- OUTPUT_TYPE（输入）：ConvType类型模板参数，指定Output的参数类型信息。
- BIAS_TYPE（可选输入）：ConvType类型模板参数，指定Bias的参数类型信息。
- CONV_CFG（可选输入）：ConvParam类型模板参数，用于开启不同场景的性能优化模板，当前版本只支持基础模板，不开启性能优化。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
