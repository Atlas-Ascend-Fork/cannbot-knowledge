---
type: API
title: SetGroups
description: 设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetGroups.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGroups

设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。

函数原型：void SetGroups(int64_t groups)

参数：
- groups（输入）：当前仅支持取值为1，暂不支持分组卷积。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetGroups》的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`same_topic`）：《Conv3D Tiling使用说明》给出“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”；该约束/探针可直接复现、解释或前置验证《SetGroups》中的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetGroups》的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《SetGroups》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
