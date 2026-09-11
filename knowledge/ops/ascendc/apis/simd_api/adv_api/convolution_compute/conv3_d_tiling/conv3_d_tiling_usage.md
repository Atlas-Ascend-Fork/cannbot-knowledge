---
type: API
title: Conv3D Tiling使用说明
description: Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/Conv3D_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# Conv3D Tiling使用说明

Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子核函数（Kernel）计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取[Init](../conv3_d_kernel/init.md)中TConv3DApiTiling结构体中的相关参数。

Conv3D Tiling API提供Conv3D单核Tiling接口，用于Conv3D单核计算场景，获取Tiling参数的流程如下：

1.  创建一个单核Tiling对象。
2.  设置Input、Weight、Bias、Output的参数类型信息以及Shape信息，如果存在Padding、Stride、Dilation参数，通过[SetPadding](set_padding.md)、[SetStride](set_stride.md)、[SetDilation](set_dilation.md)接口进行相关设置。
3.  调用[GetTiling](get_tiling.md)接口，获取Tiling信息。

使用Conv3D Tiling接口获取Tiling参数的样例如下：

```
// 实例化Conv3D Api
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
Conv3dTilingApi::Conv3dTiling conv3dApiTiling(ascendcPlatform);
// 设置输入输出原始规格、单核规格、参数等
conv3dApiTiling.SetGroups(groups);
conv3dApiTiling.SetOrgWeightShape(cout, kd, kh, kw);
conv3dApiTiling.SetOrgInputShape(cin, di, hi, wi);
conv3dApiTiling.SetPadding(padh, padt, padu, padd, padl, padr);
conv3dApiTiling.SetDilation(dilationH, dilationW, dilationD);
conv3dApiTiling.SetStride(strideH, strideW, strideD);
conv3dApiTiling.SetSingleWeightShape(cin, kd, kh, kw);
conv3dApiTiling.SetSingleOutputShape(singleCoreCo, singleCoreDo, singleCoreMo);
// 设置输入输出type
conv3dApiTiling.SetInputType(TPosition::GM, inputFormat, inputDtype);
conv3dApiTiling.SetWeightType(TPosition::GM, weightFormat, weightDtype);
conv3dApiTiling.SetOutputType(TPosition::CO1, outputFormat, outputDtype);
if (biasFlag) {
    conv3dApiTiling.SetBiasType(TPosition::GM, biasFormat, biasDtype);
}
// 调用GetTiling接口获取核内切分策略，如果返回-1代表获取tiling失败
if (conv3dApiTiling.GetTiling(tilingData.conv3dApiTilingData) == -1) {
    return false;
}
```

## 需要包含的头文件

```
#include "lib/conv/conv3d/conv3d_tiling.h"
```



<!-- cannbot:related:start -->
## 相关

- [Conv3DUsage](../conv3_d_kernel/conv3_d_usage.md)（`related`）：Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。；Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。Kernel 使用说明与 Tiling 使用说明共同覆盖 Host 参数生产和 Device 计算消费。
- [GetTiling](get_tiling.md)（`related`）：获取Tiling参数。；Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。前者是最终求解接口，后者给出参数准备到 TConv3DApiTiling 消费的完整 Host 侧使用链。
- [SetDilation](set_dilation.md)（`related`）：接口卡给出“函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)”；使用说明要求“如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。”，把三个 dilation 维度参数放入 Conv3D Tiling 的调用顺序。
- [SetPadding](set_padding.md)（`related`）：接口卡的“设置Pad信息。”说明 SetPadding 的单一职责；使用说明要求“如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。”，把它放入 GetTiling 前的参数组装顺序。
- [SetWeightType](set_weight_type.md)（`related`）：设置Weight在内存上的位置、数据格式和数据类型；设置Input、Weight、Bias、Output的参数类型信息以及Shape信息；使用说明把 SetWeightType 放入生成 Conv3D 单核 tiling 的完整配置步骤。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`related`）：结构体卡指出“用户通过调用GetTiling接口获取TConv3DApiTiling结构体，具体流程请参考Conv3D Tiling使用说明。”；使用说明给出“调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，把结构体字段接到对象创建、参数设置、GetTiling 和 Kernel Init 的完整调用顺序。
- [卷积计算Init](../conv3_d_kernel/init.md)（`related`）：Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。 Conv3D Tiling API提供Conv3D单核Tiling接口，用于Conv3D单核计算场景，获取Tiling参数的流程如下： 1. 创建一个单核Tiling对象。 2. 设置Input、Weight、Bias、Output的参数类型信息以及Shape信息，如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。；参数： - cubeTiling（输入）：Conv3D对象的Tiling参数，Tiling结构体定义请参见TConv3DApiTiling结构体。 Tiling参数可以通过Host侧GetTiling接口获取，并传递到Kernel侧使用。；焦点描述 Host 侧参数获取，目标明确同一结构体通过 Init 进入 Kernel 并触发资源划分。
<!-- cannbot:related:end -->
