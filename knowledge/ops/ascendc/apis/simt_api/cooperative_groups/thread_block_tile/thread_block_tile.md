---
type: API
title: ThreadBlockTile
description: SIMT协作线程组thread_block_tile接口集合，涵盖构造、同步、shuffle和投票等分块操作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/thread_block_tile.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile

thread_block_tile是模板类，用于管理指定大小的线程子组。提供sync同步、size/num_threads查询线程数、thread_rank/meta_group_rank/meta_group_size查询排名与分组信息。
shuffle操作含shfl/shfl_up/shfl_down/shfl_xor实现线程间数据交换。投票操作含ballot/any/all。
约束：Size<=32（单Warp内）时支持全部接口；Size>32（跨Warp）时ballot/shfl_up/shfl_down/shfl_xor不支持。一个Warp内各协作组间应避免数据依赖，否则可能卡死。

<!-- cannbot:related:start -->
## 相关

- [ThreadBlock](../thread_block/thread_block.md)（`related`）：tile 是 thread_block 的子分组，只有需要更小协作范围时才使用，不能替代全 block 屏障。
- [ThreadBlockTile协作组sync](sync.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlockTile》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [协作组](../cooperative_groups.md)（`related`）：ThreadBlockTile 是 cooperative_groups 提供的固定大小线程块子组，用于组内同步与 shuffle。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《ThreadBlockTile》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [MetaGroupSize](meta_group_size.md)（`same_topic`）：tile 对象界定 meta-group 查询的参与范围。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《ThreadBlockTile》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ShflDown](shfl_down.md)（`same_topic`）：tile 对象界定 shfl_down 的宽度和合法 lane。
- [ThreadBlockTile协作组any](any.md)（`same_topic`）：tile 对象界定 Any 的参与线程集合。
<!-- cannbot:related:end -->
