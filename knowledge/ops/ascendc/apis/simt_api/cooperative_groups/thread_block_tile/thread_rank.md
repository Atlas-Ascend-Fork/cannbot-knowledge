---
type: API
title: ThreadRank
description: 获取当前线程在所属的thread_block_tile组内的排名，排名从0开始。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadRank

获取当前线程在所属的thread_block_tile组内的排名，排名从0开始。
函数原型：unsigned long long thread_rank() const
返回值：当前线程在所属的thread_block_tile组内的排名。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《ThreadRank》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadRank](../thread_block/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
<!-- cannbot:related:end -->
