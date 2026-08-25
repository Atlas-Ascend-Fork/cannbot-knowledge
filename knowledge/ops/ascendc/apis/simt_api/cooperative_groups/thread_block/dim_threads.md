---
type: API
title: DimThreads
description: 获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/dim_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# DimThreads

获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。
函数原型：static dim3 dim_threads()
返回值：当前线程所属线程块的线程配置。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
