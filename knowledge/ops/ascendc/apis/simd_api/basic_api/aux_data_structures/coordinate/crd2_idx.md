---
type: API
title: Crd2Idx
description: 将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/Crd2Idx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Crd2Idx

将Coordinate坐标转换为Tensor中的线性索引（index）。给定多维坐标和Tensor的shape信息，计算对应的线性偏移量。

函数原型提供基于TensorDesc和基于shape数组的两种方式。参数包含coord输入坐标、tensorDesc或shape信息。返回值为线性索引。用于通过多维坐标定位Tensor元素。
