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

- [MetaGroupRank](coalesced_group/meta_group_rank.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《tiled_partition》说明将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [MetaGroupRank](thread_block_tile/meta_group_rank.md)（`related`）：MetaGroupRank 的语义来自 tiled_partition 对父组的实际划分；目标卡给出可选 Size、整除条件和跨 Warp memory 约束。
- [ThreadBlockTile协作组sync](thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《tiled_partition》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [binary_partition](binary_partition.md)（`related`）：《binary_partition》明确“根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。”；它与《tiled_partition》的“将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。”在实际调用参数、数据流或结果校验上直接衔接。
- [coalesced_group简介](coalesced_group/coalesced_group_intro.md)（`related`）：coalesced_group简介 与《tiled_partition》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [thread_block_tile简介](thread_block_tile/thread_block_tile_intro.md)（`related`）：thread_block_tile 实例由 tiled_partition 从父线程组切分得到；未完成该切分就无法调用 tile 的 sync/shfl/ballot。
- [Ballot](thread_block_tile/ballot.md)（`same_topic`）：Ballot 与《tiled_partition》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [NumThreads](thread_block_tile/num_threads.md)（`same_topic`）：NumThreads 与《tiled_partition》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [thread_block_tile构造函数](thread_block_tile/thread_block_tile_constructor.md)（`same_topic`）：《thread_block_tile构造函数》明确“thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。”；它与《tiled_partition》的“将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
