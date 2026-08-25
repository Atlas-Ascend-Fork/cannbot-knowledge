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
