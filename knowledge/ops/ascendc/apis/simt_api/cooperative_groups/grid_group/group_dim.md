---
type: API
title: GroupDim
description: 获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/group_dim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GroupDim

获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
函数原型：static dim3 group_dim()
返回值：当前Grid的线程块维度配置。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [DimBlocks](dim_blocks.md)（`same_topic`）：获取当前Grid的线程块维度配置。；获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。。两卡明确返回相同 Grid 线程块维度，group_dim 是 dim_blocks 的同功能接口。
<!-- cannbot:related:end -->
