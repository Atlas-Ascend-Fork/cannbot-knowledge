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

- [MetaGroupSize](meta_group_size.md)（`related`）：MetaGroupSize 不是 tile 内线程数，NumThreads 查询另一维度。
- [Ballot](ballot.md)（`same_topic`）：NumThreads 与《Ballot》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [MetaGroupRank](meta_group_rank.md)（`same_topic`）：NumThreads 与《MetaGroupRank》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [NumThreads](../coalesced_group/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [NumThreads](../grid_group/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [NumThreads](../thread_block/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadBlockTile](thread_block_tile.md)（`same_topic`）：NumThreads 与《ThreadBlockTile》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadBlockTile协作组size](size.md)（`same_topic`）：NumThreads 与《ThreadBlockTile协作组size》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadRank](thread_rank.md)（`same_topic`）：NumThreads 与《ThreadRank》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [thread_block_tile构造函数](thread_block_tile_constructor.md)（`same_topic`）：NumThreads 与《thread_block_tile构造函数》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [thread_block_tile简介](thread_block_tile_intro.md)（`same_topic`）：NumThreads 与《thread_block_tile简介》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [tiled_partition](../tiled_partition.md)（`same_topic`）：NumThreads 与《tiled_partition》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [协作组](../cooperative_groups.md)（`same_topic`）：NumThreads 与《协作组》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
<!-- cannbot:related:end -->
