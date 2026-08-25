---
type: API
title: DimBlocks
description: 获取当前Grid的线程块维度配置。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/dim_blocks.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# DimBlocks

获取当前Grid的线程块维度配置。
函数原型：static dim3 dim_blocks()
返回值：当前Grid的线程块维度配置。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumBlocks](num_blocks.md)（`related`）：DimBlocks说明获取当前Grid的线程块维度配置。
- [GroupDim](group_dim.md)（`same_topic`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“DimBlocks”定义：获取当前Grid的线程块维度配置。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
<!-- cannbot:related:end -->
