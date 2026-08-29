---
type: API
title: SetAippFunctions
description: 设置图片预处理（AIPP）相关参数，与LoadImageToLocal接口配合使用，支持数据填充、通道交换、单行读取、数据类型转换、通道填充和色域转换等功能。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetAippFunctions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetAippFunctions

设置图片预处理（AIPP，AI Core pre-process）参数，与 LoadImageToLocal 配合使用。调用时需传入源图片在 GM 上的矩阵和图片格式。设置后 LoadImageToLocal 可在搬运中完成：数据填充、通道交换、单行读取、数据类型转换、通道填充、色域转换。

数据填充支持 4 种模式：模式 0 常量填充（仅左右 padding，每通道可设不同常数）、模式 1 行列填充（取最邻近源图数据）、模式 2 块填充（从源图拷贝数据块）、模式 3 镜像块填充（拷贝数据块镜像）。色域转换支持 RGB↔YUV 等。通道交换可配置输出通道顺序。

支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core，不支持 Vector Core 和 Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [LoadImageToLocal](load_image_to_local.md)（`related`）：将图像数据从 Global Memory 搬运到 Local Memory，搬运过程中可完成图像预处理（翻转、抠图、裁边、缩放、伸展、色域转换、类型转换）。预处理参数通过 SetAippFunctions 配置。；设置图片预处理（AIPP，AI Core pre-process）参数，与 LoadImageToLocal 配合使用。调用时需传入源图片在 GM 上的矩阵和图片格式。。LoadImageToLocal 卡指出搬运中预处理由 SetAippFunctions 配置，配置卡又明确其必须与 LoadImageToLocal 配合，二者是同一 AIPP 搬运流程的配置端与执行端。
<!-- cannbot:related:end -->
