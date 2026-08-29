---
type: API
title: Conv3DUsage
description: Ascend C提供Conv3D高阶API，用于快速实现3维卷积正向矩阵运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3D_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DUsage

Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。3维正向卷积的示意图如图1，其计算公式为： - X为Conv3D卷积的特征矩阵Input。 - W为Conv3D卷积的权重矩阵Weight。 - B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。 图1 3维正向卷积示意图

<!-- cannbot:related:start -->
## 相关

- [Conv3D Kernel侧接口](conv3d_kernel.md)（`related`）：Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。；提供三维卷积前向计算的 Kernel 侧接口，基于模板参数配置输入、权重、偏置的数据类型与排布格式。使用说明给出完整调用场景，接口页给出 Init、SetInput、IterateAll 等可执行合同，能从任务步骤落到具体 Kernel API。
- [Conv3D Tiling使用说明](../conv3_d_tiling/conv3_d_tiling_usage.md)（`related`）：Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。；Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。Kernel 使用说明与 Tiling 使用说明共同覆盖 Host 参数生产和 Device 计算消费。
- [SetBias](set_bias.md)（`related`）：bias（输入）：Bias在Global Memory上的地址。类型为GlobalTensor。偏置矩阵Bias支持的数据类型为：half、bfloat16_t。；B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。。SetBias 的输入合同把 usage 中卷积偏置 B 的 GM 地址和支持 dtype 落到具体配置接口。
<!-- cannbot:related:end -->
