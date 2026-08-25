---
type: API
title: CoalescedGroup协作组sync
description: 同步coalesced_group组内所有线程。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup协作组sync

同步coalesced_group组内所有线程。
函数原型：void sync() const
约束：必须保证coalesced_group组内所有线程都能执行到同一个sync()调用，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ballot](ballot.md)（`related`）：Ballot 等组内集体操作前若存在数据依赖，需要用同一组的 sync 建立可见性和执行汇合。
- [ThreadBlockTile协作组sync](../thread_block_tile/sync.md)（`related`）：ThreadBlockTile sync 同样要求组内线程一致到达，但作用域是静态 tile，可与动态 coalesced group 对照选型。
- [binary_partition](../binary_partition.md)（`related`）：binary_partition 与《CoalescedGroup协作组sync》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
- [coalesced_group简介](coalesced_group_intro.md)（`same_topic`）：简介说明 coalesced_group 由当前活跃线程动态形成，是理解 sync 必须全组到达的作用域基础。
- [sync（协作组）](../sync.md)（`same_topic`）：coalesced_group 版本同步当前收敛线程集合；分支发散后的组成员语义与静态 tile 不同。
<!-- cannbot:related:end -->
