---
type: API
title: ThreadBlock
description: SIMT协作线程组thread_block接口集合，涵盖构造、同步、线程索引和维度查询等操作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlock

thread_block是对线程块的抽象，代表核函数的启动配置（线程块个数、每块线程数等）。提供sync同步线程块内所有线程。
查询接口含thread_rank（块内线程排名）、num_threads/size（块内线程数）、thread_index/group_index（线程与线程块索引）、dim_threads/group_dim（线程与线程块维度）。

<!-- cannbot:related:start -->
## 相关

- [GridGroup](../grid_group/grid_group.md)（`related`）：焦点处理grid_group 与 thread_block 协作范围的选择；ThreadBlock正文说明“SIMT协作线程组thread_block接口集合，涵盖构造、同步、线程索引和维度查询等操作”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [ThreadBlockTile](../thread_block_tile/thread_block_tile.md)（`related`）：tile 是 thread_block 的子分组，只有需要更小协作范围时才使用，不能替代全 block 屏障。
- [ThreadBlockTile协作组sync](../thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlock》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [协作组](../cooperative_groups.md)（`related`）：ThreadBlock 是汇总页列出的四种组之一，定义整线程块的索引、维度和块内 sync，覆盖最常用的块级协作范围。
- [DimThreads](dim_threads.md)（`same_topic`）：DimThreads 给出三维线程布局，补充 size 的总量信息。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《ThreadBlock》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadBlock协作组size](size.md)（`same_topic`）：size 查询 block 内线程总数，是 thread_block 对象最基本的消费接口。
- [ThreadBlock协作组sync](sync.md)（`same_topic`）：Sync 对整个 thread_block 建立屏障，参与范围由该 group 对象界定。
- [ThreadIndex](thread_index.md)（`same_topic`）：ThreadIndex 是 thread_block group 的坐标查询，类型页界定其作用域。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadBlock》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [thread_block构造函数](thread_block_constructor.md)（`same_topic`）：thread_block构造函数 与《ThreadBlock》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [thread_block简介](thread_block_intro.md)（`same_topic`）：介绍页定义 thread_block 的成员、同步范围和获取方式，是类型页的概念入口。
<!-- cannbot:related:end -->
