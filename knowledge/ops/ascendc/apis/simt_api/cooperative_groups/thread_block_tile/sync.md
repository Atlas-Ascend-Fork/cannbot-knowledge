---
type: API
title: ThreadBlockTile协作组sync
description: 同步当前线程所属的thread_block_tile组内的所有线程。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组sync

同步当前线程所属的thread_block_tile组内的所有线程。
函数原型：void sync() const
约束：必须保证thread_block_tile组内所有线程都能执行到同一个sync()调用，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：ThreadBlockTile协作组sync 与《SIMT协作组简介（高级编程）》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [AscThreadfenceBlock](../../sync_and_memory_fence/memory_fence/asc_threadfence_block.md)（`related`）：ThreadBlockTile协作组sync 与《AscThreadfenceBlock》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [CoalescedGroup协作组sync](../coalesced_group/sync.md)（`related`）：ThreadBlockTile sync 同样要求组内线程一致到达，但作用域是静态 tile，可与动态 coalesced group 对照选型。
- [ThreadBlock](../thread_block/thread_block.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlock》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [ThreadBlockTile](thread_block_tile.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlockTile》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [ThreadBlockTile协作组any](any.md)（`related`）：若谓词依赖前序共享数据写入，需先对同一 tile 同步再调用 Any。
- [ThreadBlock协作组sync](../thread_block/sync.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlock协作组sync》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block_tile构造函数](thread_block_tile_constructor.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block_tile构造函数》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block_tile简介](thread_block_tile_intro.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block_tile简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block简介](../thread_block/thread_block_intro.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [tiled_partition](../tiled_partition.md)（`related`）：ThreadBlockTile协作组sync 与《tiled_partition》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [协作组](../cooperative_groups.md)（`related`）：ThreadBlockTile协作组sync 与《协作组》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [协作组简介](../cooperative_groups_intro.md)（`related`）：ThreadBlockTile协作组sync 与《协作组简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组sync》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [sync（协作组）](../sync.md)（`same_topic`）：thread_block_tile 版本只同步 tile 子组，适合固定小线程协作范围。
<!-- cannbot:related:end -->
