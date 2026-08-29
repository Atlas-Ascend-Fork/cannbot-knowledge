---
type: API
title: tiled_partition
description: 将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/tiled_partition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# tiled_partition

tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。提供模板和非模板两个版本的接口，分别用于编译时确定划分大小以及运行时确定划分大小的场景。模板版本支持创建跨Warp的thread_block_tile。
函数原型：thread_block_tile<Size, ParentT> tiled_partition(const ParentT& g)
返回值：返回划分出的子组对象。
约束：模板版本的 Size 必须是 2^n，可选 1 至 2048 的 2 的幂；非模板版本只支持 Size <= 32。创建跨 Warp 的 thread_block_tile 时，block_tile_memory 必须位于 Global Memory 或 Unified Buffer，不能位于栈空间，且 Unified Buffer 性能更优。父组线程数必须能被 Size 整除；父组也是 thread_block_tile 时，Size 必须小于父组大小。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [MetaGroupRank](thread_block_tile/meta_group_rank.md)（`related`）：获取当前线程所在的组在从父组划分出的子组集合中的排名，排名从0开始。；返回值：返回划分出的子组对象。tiled_partition 生产子组集合，MetaGroupRank 在该集合中解释当前组序号，形成直接对象生产与查询链。
- [ShflUp](thread_block_tile/shfl_up.md)（`related`）：获取thread_block_tile组内当前线程向前偏移delta的线程的数据。；tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。。tiled_partition 先创建固定大小的 thread_block_tile，shfl_up 再在该组内按 delta 读取前方线程数据，形成分组到组内通信的使用链。
- [thread_block_tile构造函数](thread_block_tile/thread_block_tile_constructor.md)（`related`）：tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。；thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。前者定义划分操作，后者把该操作确定为 thread_block_tile 的构造入口。
<!-- cannbot:related:end -->
