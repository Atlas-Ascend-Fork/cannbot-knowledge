---
type: API
title: NumThreads
description: 获取当前Grid内的SIMT线程总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumThreads

获取当前Grid内的SIMT线程总数。
函数原型：static unsigned long long num_threads()
返回值：当前Grid内的SIMT线程总数。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Grid协作组size](size.md)（`same_topic`）：获取当前Grid内的SIMT线程总数，与接口num_threads功能相同。；获取当前Grid内的SIMT线程总数。。Size 正文直接声明与 NumThreads 功能相同，两者都返回当前 Grid 的 SIMT 线程总数，是同一查询契约的两个接口名称。
<!-- cannbot:related:end -->
