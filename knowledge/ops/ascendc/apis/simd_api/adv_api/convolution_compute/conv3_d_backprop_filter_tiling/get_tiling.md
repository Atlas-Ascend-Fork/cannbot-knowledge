---
type: API
title: GetTiling
description: 获取Tiling参数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.neighborhood.convolution
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# GetTiling

## 功能说明

获取Tiling参数。

## 函数原型

```
int64_t GetTiling(optiling::Conv3DBackpropFilterTilingData& tiling)
```

```
int64_t GetTiling(AscendC::tiling::Conv3DBackpropFilterTilingData& tiling)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| tiling | 输出 | TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考[TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)。 |

## 返回值说明

如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

## 约束说明

无

## 调用示例

```
#include "tiling/conv_backprop/conv3d_bp_filter_tiling.h"

optiling::Conv3DBackpropFilterTilingData tilingData;
auto ascendcPlatform = platform_ascendc::PlatformAscendCManager::GetInstance();
ConvBackpropApi::Conv3dBpFilterTiling conv3dBpDwTiling(*ascendcPlatform);
conv3dBpDwTiling.SetWeightType(
    ConvCommonApi::TPosition::GM, ConvCommonApi::ConvFormat::FRACTAL_Z_3D, ConvCommonApi::ConvDtype::FLOAT32);
conv3dBpDwTiling.SetInputType(
    ConvCommonApi::TPosition::GM, ConvCommonApi::ConvFormat::NDC1HWC0, ConvCommonApi::ConvDtype::FLOAT16);
conv3dBpDwTiling.SetGradOutputType(
    ConvCommonApi::TPosition::GM, ConvCommonApi::ConvFormat::NDC1HWC0, ConvCommonApi::ConvDtype::FLOAT16);
conv3dBpDwTiling.SetInputShape(n, c, d, h, w);
conv3dBpDwTiling.SetGradOutputShape(n, c, d, h, w);
conv3dBpDwTiling.SetWeightShape(cout, cin, d, h, w);
conv3dBpDwTiling.SetPadding(padFront, padBack, padUp, padDown, padLeft, padRight);
conv3dBpDwTiling.SetStride(strideD, strideH, strideW);
conv3dBpDwTiling.SetDilation(dilationD, dilationH, dilationW);
int ret = conv3dBpDwTiling.GetTiling(tilingData); // 获取tiling参数
// 使用AscendC::tiling命名空间中的Tiling结构体获取tiling参数
AscendC::tiling::Conv3DBackpropFilterTilingData tilingDataNotOp;
ret = conv3dBpDwTiling.GetTiling(tilingDataNotOp);
```


<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`related`）：“返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。”与“Ascend C提供一组Conv3DBackpropFilter Tiling API，方便用户获取Conv3DBackpropFilter Kernel计算时所需的Tiling参数。用户只需要传入Input/GradOutput/GradWeight的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DBpFilterTiling结构体中的相关参数。 Conv3DBackpropFilter Tiling API提供一个GetTiling接口获取Tiling参数，获取Tiling参数的流程如下：创建单核 Tiling 对象，设置 Input、GradOutput、GradWeight 的类型、Shape 及可选 Padding/Stride，最后调用 GetTiling。”。接口卡定义 GetTiling 成败语义，使用页给出设置规格后调用 GetTiling 的完整流程。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：“- tiling（输出）：TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考TConv3DBpFilterTiling结构体。”与“TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DBpFilterTiling结构体，具体流程请参考使用说明。当前暂不支持用户自定义配置TConv3DBpFilterTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。”。GetTiling 的输出正是结构体卡定义的 Kernel 切分、搬运与计算参数载体。
- [卷积计算Init](../conv3_d_backprop_filter_kernel/init.md)（`related`）：“- tiling（输出）：TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考TConv3DBpFilterTiling结构体。”与“Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropFilter Tiling侧接口。”。Tiling 接口生产 TConv3DBpFilterTiling，Kernel Init 消费它完成资源划分。
<!-- cannbot:related:end -->
