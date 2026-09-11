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
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/GetTiling.md
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
int64_t GetTiling(optiling::TConv3DApiTiling& tiling)
```

```
int64_t GetTiling(AscendC::tiling::TConv3DApiTiling& tiling)
```

## 参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| tiling | 输出 | Conv3D的Tiling结构体，用于存储最终的Tiling结果。TConv3DApiTiling结构介绍请参考[TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)。 |

## 返回值说明

如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

## 约束说明

调用GetTiling接口前必须先调用SetOrgInputShape、SetOrgWeightShape、SetSingleWeightShape、SetSingleOutputShape。

## 调用示例

```
// 实例化Conv3d Api
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
Conv3dTilingApi::Conv3dTiling conv3dApiTiling(ascendcPlatform);
conv3dApiTiling.SetOrgInputShape(orgCi, orgDi, orgHi, orgWi);
conv3dApiTiling.SetOrgWeightShape(cout, kd, kh, kw);
conv3dApiTiling.SetSingleWeightShape(singleCi, singleKd, singleKh, singleKw);
conv3dApiTiling.SetSingleOutputShape(singleCo, singleDo, singleM);
...
conv3dApiTiling.GetTiling(tilingData.conv3ApiTilingData);
```


<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：获取Tiling参数。；Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。前者是最终求解接口，后者给出参数准备到 TConv3DApiTiling 消费的完整 Host 侧使用链。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`related`）：结构体卡说明“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。”；GetTiling 卡规定“tiling（输出）：Conv3D的Tiling结构体，用于存储最终的Tiling结果。”，明确了该结构体的 Host 生产接口。
- [卷积计算Init](../conv3_d_kernel/init.md)（`related`）：焦点卡规定“Tiling参数可以通过Host侧GetTiling接口获取，并传递到Kernel侧使用”，候选卡说明“如果返回值不为-1，则代表Tiling计算成功”；两卡组成 Host 生成并校验 Tiling、再交给 Kernel Init 的直接参数链。
<!-- cannbot:related:end -->
