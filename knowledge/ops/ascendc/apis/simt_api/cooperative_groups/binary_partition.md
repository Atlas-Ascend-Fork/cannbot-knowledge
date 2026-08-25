---
type: API
title: binary_partition
description: 根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/binary_partition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# binary_partition

binary_partition API用于根据一个标签（0或1）将父组划分为两个子组，标签相同的线程会被分配到同一组中。
函数原型：coalesced_group binary_partition(const coalesced_group& g, bool pred)
返回值：返回划分出的子组coalesced_group对象。
约束：当g为thread_block_tile类型时，g必须满足Size小于等于32，否则编译报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup协作组size](coalesced_group/size.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《binary_partition》说明根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [CoalescedGroup协作组sync](coalesced_group/sync.md)（`related`）：binary_partition 与《CoalescedGroup协作组sync》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
- [MetaGroupRank](coalesced_group/meta_group_rank.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《binary_partition》说明根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [MetaGroupSize](coalesced_group/meta_group_size.md)（`related`）：binary_partition 与《MetaGroupSize》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
- [coalesced_group简介](coalesced_group/coalesced_group_intro.md)（`related`）：coalesced_group简介 与《binary_partition》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [tiled_partition](tiled_partition.md)（`related`）：《binary_partition》明确“根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。”；它与《tiled_partition》的“将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。”在实际调用参数、数据流或结果校验上直接衔接。
- [协作组简介](cooperative_groups_intro.md)（`related`）：协作组简介明确把 binary_partition 列为按 0/1 标签划分父组的操作，后者给出 coalesced_group 返回值和 tile 大小约束。
- [Ballot](thread_block_tile/ballot.md)（`same_topic`）：Ballot 与《binary_partition》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [协作组](cooperative_groups.md)（`same_topic`）：binary_partition 与《协作组》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
<!-- cannbot:related:end -->
