---
type: API
title: NumThreads
description: 获取当前线程所属线程块内的线程总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumThreads

获取当前线程所属线程块内的线程总数。
函数原型：static unsigned int num_threads()
返回值：当前线程所属线程块内的线程总数，即blockDim.x  blockDim.y  blockDim.z。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ThreadBlock协作组size](size.md)（`same_topic`）：获取当前线程所属线程块内的线程总数。；获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。。size 正文明确声明与 num_threads 功能相同，两卡是同一 thread_block 线程数查询的两个接口名。
<!-- cannbot:related:end -->
