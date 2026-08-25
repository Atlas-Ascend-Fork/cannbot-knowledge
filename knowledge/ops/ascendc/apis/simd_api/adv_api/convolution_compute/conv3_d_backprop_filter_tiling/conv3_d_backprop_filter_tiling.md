---
type: API
title: Conv3DBackpropFilter Tiling侧接口
description: 提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/Conv3DBackpropFilter_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropFilter Tiling侧接口

提供 Conv3D 反向滤波器梯度的 Host 侧 Tiling 接口，通过 TConv3DBpFilterTiling 结构体承载切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetWeightShape/SetInputShape/SetGradOutputShape 设置各张量形状，SetWeightType/SetInputType/SetGradOutputType 设置数据类型。
另提供 SetPadding/SetStride/SetDilation 设置卷积超参数，使用前需通过构造函数初始化 Tiling 对象。
