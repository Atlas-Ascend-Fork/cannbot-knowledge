---
type: API
title: MetaGroupRank
description: 获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/meta_group_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MetaGroupRank

获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。
函数原型：unsigned long long meta_group_rank() const
返回值：当前线程所在的组在从父组划分出的子组集合中的排名。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [MetaGroupSize](meta_group_size.md)（`related`）：MetaGroupRank 给出当前 tile 在父组划分结果中的序号，MetaGroupSize 给出该次划分产生的子组总数；二者共同支持对子组做分片和边界判断。
- [tiled_partition](../tiled_partition.md)（`related`）：MetaGroupRank 的语义来自 tiled_partition 对父组的实际划分；目标卡给出可选 Size、整除条件和跨 Warp memory 约束。
- [MetaGroupRank](../coalesced_group/meta_group_rank.md)（`same_topic`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《MetaGroupRank》说明获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《MetaGroupRank》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
<!-- cannbot:related:end -->
