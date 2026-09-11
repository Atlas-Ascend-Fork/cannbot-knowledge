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
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/GetTiling.md
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
int64_t GetTiling(optiling::Conv3DBackpropInputTilingData& tiling)
```

```
int64_t GetTiling(AscendC::tiling::Conv3DBackpropInputTilingData& tiling)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| tiling | 输出 | Conv3DBackpropInput的Tiling结构体，用于存储最终的Tiling结果。TConv3DBackpropInputTiling结构介绍请参考[TConv3DApiTiling结构体说明](t_conv3_d_backprop_input_tiling_struct.md)。 |

## 返回值说明

如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

## 约束说明

无

## 调用示例

```
// 构建Conv3dBackpropInput算子tiling的调用示例
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
ConvBackpropApi::Conv3DBpInputTiling tiling(ascendcPlatform);
tiling.SetWeightShape(256, 128, 3, 3, 3);
tiling.SetInputShape(1, 128, 11, 128, 128);
tiling.SetGradOutputShape(1, 256, 9, 128, 128);
tiling.SetPadding(0, 0, 1, 1, 1, 1);
tiling.SetDilation(1, 1, 1);
tiling.SetStride(1, 1, 1);
optiling::Conv3DBackpropInputTilingData tilingData;
int ret = tiling.GetTiling(tilingData); // 获取Tiling参数
AscendC::tiling::Conv3DBackpropInputTilingData tilingDataNotOp;
ret = tiling.GetTiling(tilingDataNotOp); // 使用AscendC::tiling::Conv3DBackpropInputTilingData获取Tiling参数
```

```
// 构建Conv3dTranspose算子tiling的调用示例
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
ConvBackpropApi::Conv3DBpInputTiling tiling(ascendcPlatform);
tiling.SetWeightShape(256, 128, 3, 3, 3);
tiling.SetGradOutputShape(256, 9, 128, 128); // 等价于Conv3dTranspose的输入X
tiling.SetPadding(0, 0, 1, 1, 1, 1);
tiling.SetDilation(1, 1, 1);
tiling.SetStride(1, 1, 1);
tiling.SetOutputPadding(0, 0, 0); // 对Conv3dTranspose的输出Y进行padding
optiling::Conv3DBackpropInputTilingData tilingData;
int ret = tiling.GetTiling(tilingData); // 获取Tiling参数
```


<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`related`）：“Conv3DBackpropInput Tiling API提供一个GetTiling接口获取Tiling参数”给出焦点端事实；“如果返回值不为-1，则代表Tiling计算成功”给出候选端事实。使用卡把 GetTiling 放进 Conv3DBackpropInput Tiling 的实际调用流程，接口卡给出返回值成功判据，二者闭合调用与验证。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`related`）：TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。；- tiling（输出）：Conv3DBackpropInput的Tiling结构体，用于存储最终的Tiling结果。TConv3DBackpropInputTiling结构介绍请参考TConv3DApiTiling结构体说明。。结构体卡定义 Kernel 消费的数据结构，GetTiling 卡定义产生该结构体的 Host 输出，构成明确的生产与消费合同。
<!-- cannbot:related:end -->
