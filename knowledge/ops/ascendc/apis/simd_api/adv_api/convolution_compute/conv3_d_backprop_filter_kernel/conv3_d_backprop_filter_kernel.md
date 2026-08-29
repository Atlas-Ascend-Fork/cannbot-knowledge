---
type: API
title: Conv3DBackpropFilter Kernel侧接口
description: 提供Conv3D反向卷积滤波器梯度的Kernel侧接口，包含Init、SetInput、SetGradOutput、Iterate等方法及使用说明。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Conv3DBackpropFilter_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropFilter Kernel侧接口

提供三维卷积反向滤波器梯度计算的 Kernel 侧接口。
核心方法包括 Init 初始化、SetInput 设置前向输入、SetGradOutput 设置梯度输出、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。
计算过程中通过 Iterate 循环分块处理，最终通过 GetTensorC 获取滤波器梯度结果。
