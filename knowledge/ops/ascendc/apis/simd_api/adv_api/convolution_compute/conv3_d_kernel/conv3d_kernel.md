---
type: API
title: Conv3D Kernel侧接口
description: 提供Conv3D前向计算的Kernel侧接口，包含Init、SetInput、SetWeight、IterateAll等方法及模板参数与使用说明。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3d_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D Kernel侧接口

提供三维卷积前向计算的 Kernel 侧接口，基于模板参数配置输入、权重、偏置的数据类型与排布格式。
核心方法包括 Init 初始化、SetInput/SetWeight/SetBias 设置输入张量、SetSingleOutputShape 设置单次输出形状、SetInputStartPosition 设置输入起始位置、IterateAll 执行全部迭代、End 释放资源。
使用前需通过模板参数指定 TPosition、数据类型及 Layout 等配置，具体约束参见 Conv3D 使用说明。
