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
