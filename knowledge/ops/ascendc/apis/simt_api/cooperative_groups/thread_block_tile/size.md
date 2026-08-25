---
type: API
title: ThreadBlockTile协作组size
description: 获取协作组内线程的总数，功能与num_threads函数一致。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组size

获取协作组内线程的总数，功能与num_threads函数一致。
函数原型：unsigned long long size() const
返回值：协作组内线程的总数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ballot](ballot.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组size》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《ThreadBlockTile协作组size》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
<!-- cannbot:related:end -->
