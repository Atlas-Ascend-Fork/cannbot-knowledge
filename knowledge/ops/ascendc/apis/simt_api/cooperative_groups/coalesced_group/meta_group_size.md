---
type: API
title: MetaGroupSize
description: 获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/meta_group_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MetaGroupSize

获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。
函数原型：unsigned long long meta_group_size() const
返回值：直接父组被划分时创建的子组的数量。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [MetaGroupRank](meta_group_rank.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《MetaGroupSize》说明获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [binary_partition](../binary_partition.md)（`related`）：binary_partition 与《MetaGroupSize》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
- [MetaGroupSize](../thread_block_tile/meta_group_size.md)（`same_topic`）：coalesced_group 与 tile 都可查询 meta-group 大小，但 group 形成方式不同。
- [coalesced_group简介](coalesced_group_intro.md)（`same_topic`）：coalesced_group简介 与《MetaGroupSize》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
<!-- cannbot:related:end -->
