---
type: API
title: Conv3DBackpropFilter使用说明
description: Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Conv3DBackpropFilter_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropFilter使用说明

Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。 卷积反向的权重传播如图1，卷积反向权重计算如图2。 Conv3dBackpropFilter的计算公式为： - X为卷积的特征矩阵Input。 - ∂L/∂Y为卷积正向损失函数对输出Y的梯度GradOutput，作为求反向传播误差∂L/∂W的输入，即卷积的输出反向GradOutput。 - ∂L/∂W为Weight权重的反向传播误差GradWeight。 图1 卷积反向权重传播示意图 图2 卷积反向权重计算过程示意图 Kernel侧实现Conv3DBackpropFilter求解反向传播误差运算的步骤概括为：
