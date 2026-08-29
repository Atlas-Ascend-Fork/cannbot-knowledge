---
type: API
title: NumThreads
description: 获取当前线程所属的thread_block_tile组内的线程总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumThreads

获取当前线程所属的thread_block_tile组内的线程总数。
函数原型：unsigned long long num_threads() const
返回值：当前线程所属的thread_block_tile组内的线程总数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ThreadBlockTile协作组size](size.md)（`same_topic`）：获取协作组内线程的总数，功能与num_threads函数一致。；获取当前线程所属的thread_block_tile组内的线程总数。。size 文档直接声明与 num_threads 功能一致，两者是同一 thread_block_tile 线程总数查询的别名入口。
<!-- cannbot:related:end -->
