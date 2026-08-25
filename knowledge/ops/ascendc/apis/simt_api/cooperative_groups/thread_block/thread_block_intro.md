---
type: API
title: thread_block简介
description: thread_block是对线程块的抽象，它代表了核函数的启动配置（启动的线程块个数，每个线程块内的线程数量等）。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# thread_block简介

thread_block是对线程块的抽象，它代表了核函数的启动配置（启动的线程块个数，每个线程块内的线程数量等）。通过thread_block可查询线程块维度、线程排名，并调用sync()在线程块范围内同步。

Public成员函数：sync、thread_rank、group_index、thread_index、dim_threads、num_threads、size、group_dim。头文件：simt_api/cooperative_groups.h。

<!-- cannbot:related:start -->
## 相关

- [ThreadBlockTile协作组sync](../thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block_tile简介](../thread_block_tile/thread_block_tile_intro.md)（`related`）：thread_block 管理整个线程块，而 thread_block_tile 以模板 Size 划分子组并限制跨 Warp 的 ballot/shuffle；共享数据范围决定同步和通信作用域。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《thread_block简介》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadBlock](thread_block.md)（`same_topic`）：介绍页定义 thread_block 的成员、同步范围和获取方式，是类型页的概念入口。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank 与《thread_block简介》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [thread_block构造函数](thread_block_constructor.md)（`same_topic`）：thread_block构造函数 与《thread_block简介》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
<!-- cannbot:related:end -->
