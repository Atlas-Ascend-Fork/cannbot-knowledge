---
type: API
title: Conv2D（废弃）
description: 该接口废弃，并将在后续版本移除，请不要使用该接口。 计算给定输入张量和权重张量的2-D卷积，输出结果张量。Conv2D卷积层多用于图像识别，使用过滤器提取图像中的特征。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Conv2D_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Conv2D（废弃）

该接口已废弃，将在后续版本移除，请勿使用。计算输入张量和权重张量的 2D 卷积，输出结果张量，多用于图像识别中的特征提取。

原型：Conv2D(dst, featureMap, weight, conv2dParams, tilling)，tiling 通过 GetConv2DTiling(conv2dParams) 获取。仅 Atlas 推理系列产品 AI Core 和 Atlas 训练系列产品曾支持。请使用 Mmad 等接口替代。

<!-- cannbot:related:start -->
## 相关

- [Mmad](mmad.md)（`related`）：Mmad说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`same_topic`）：废弃接口说明列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [矩阵计算（ISASI）](mmad_compute.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Conv2D（废弃）》补充：该接口废弃，并将在后续版本移除，请不要使用该接口。 计算给定输入张量和权重张量的2-D卷积，输出结果张量。Conv2D卷积层多用于图像识别，使用过滤器提取图像中的特征。
<!-- cannbot:related:end -->
