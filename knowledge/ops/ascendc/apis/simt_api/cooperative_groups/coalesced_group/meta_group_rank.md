---
type: API
title: MetaGroupRank
description: 获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/meta_group_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MetaGroupRank

获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。
函数原型：unsigned long long meta_group_rank() const
返回值：当前线程所在的组在其父组划分出的子组集合中的排名。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [MetaGroupSize](meta_group_size.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《MetaGroupSize》说明获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [binary_partition](../binary_partition.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《binary_partition》说明根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [tiled_partition](../tiled_partition.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《tiled_partition》说明将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [MetaGroupRank](../thread_block_tile/meta_group_rank.md)（`same_topic`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《MetaGroupRank》说明获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
<!-- cannbot:related:end -->
