---
type: API
title: thread_block_tile简介
description: thread_block_tile是一个模板类，用于管理指定大小的线程子组。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/thread_block_tile_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# thread_block_tile简介

thread_block_tile是一个模板类，用于管理指定大小的线程子组。通过模板参数Size指定子组线程数量，支持sync同步、thread_rank查询线程排名、shfl/shfl_up/shfl_down/shfl_xor线程间数据交换、any/all/ballot谓词归约等操作。

接口支持范围：当Size<=32（单Warp内）时所有接口均支持；当Size>32（跨Warp）时ballot、shfl_up、shfl_down、shfl_xor不支持。

约束：SIMT架构不支持独立线程调度，一个Warp内的各协作组间应避免存在数据依赖，否则可能出现卡死的情况。

<!-- cannbot:related:start -->
## 相关

- [ThreadBlockTile协作组sync](sync.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block_tile简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block简介](../thread_block/thread_block_intro.md)（`related`）：thread_block 管理整个线程块，而 thread_block_tile 以模板 Size 划分子组并限制跨 Warp 的 ballot/shuffle；共享数据范围决定同步和通信作用域。
- [tiled_partition](../tiled_partition.md)（`related`）：thread_block_tile 实例由 tiled_partition 从父线程组切分得到；未完成该切分就无法调用 tile 的 sync/shfl/ballot。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《thread_block_tile简介》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《thread_block_tile简介》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [thread_block_tile构造函数](thread_block_tile_constructor.md)（`same_topic`）：《thread_block_tile简介》明确“thread_block_tile是一个模板类，用于管理指定大小的线程子组。”；它与《thread_block_tile构造函数》的“thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
