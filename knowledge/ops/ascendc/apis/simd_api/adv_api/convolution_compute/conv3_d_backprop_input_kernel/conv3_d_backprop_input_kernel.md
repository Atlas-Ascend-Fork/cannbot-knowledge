---
type: API
title: Conv3DBackpropInput Kernel侧接口
description: 提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/Conv3DBackpropInput_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropInput Kernel侧接口

提供三维卷积反向输入梯度计算的 Kernel 侧接口。
核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。
与前向 Conv3D Kernel 接口相比，输入侧改为接收梯度输出与权重，输出为输入梯度。
