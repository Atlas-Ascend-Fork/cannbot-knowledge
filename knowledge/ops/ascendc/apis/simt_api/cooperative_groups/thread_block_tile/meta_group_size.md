---
type: API
title: MetaGroupSize
description: 获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/meta_group_size.md
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

- [MetaGroupRank](meta_group_rank.md)（`related`）：MetaGroupRank 给出当前 tile 在父组划分结果中的序号，MetaGroupSize 给出该次划分产生的子组总数；二者共同支持对子组做分片和边界判断。
- [NumThreads](num_threads.md)（`related`）：MetaGroupSize 不是 tile 内线程数，NumThreads 查询另一维度。
- [MetaGroupSize](../coalesced_group/meta_group_size.md)（`same_topic`）：coalesced_group 与 tile 都可查询 meta-group 大小，但 group 形成方式不同。
- [ThreadBlockTile](thread_block_tile.md)（`same_topic`）：tile 对象界定 meta-group 查询的参与范围。
<!-- cannbot:related:end -->
