---
type: API
title: 协作组简介
description: 协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/cooperative_groups_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 协作组简介

协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作。
协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作。

当前提供协作组类型有：

- thread_block：对线程块的抽象，提供统一的线程管理接口。
- coalesced_group：Warp中的活跃线程集合。
- thread_block_tile：手动划分出的线程子组。
- grid_group：对一个核函数启动的所有SIMT线程的抽象，提供跨线程块的查询和同步接口。

基于以上协作组类型，提供以下划分操作，支持将一个协作组划分为多个子组：

- tiled_partition：将父组划分成指定大小的子组。
- binary_partition：根据自定义的0、1标签将父组划分为两个子组。

基于以上协作组类型，提供以下通用操作：

- sync：同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：高级指南给出隐式/显式组、作用域选择和使用方法；API 简介补齐 tiled_partition/binary_partition 及通用 sync，是同一 cooperative_groups 模型的接口入口。
- [GridGroup](grid_group/grid_group.md)（`related`）：焦点处理grid_group 与 thread_block 协作范围的选择；协作组简介正文说明“协作组（cooperative_groups）是Ascend C SIMT编程模型的一种拓展，用于组织协作线程组。通过协作组能够更细粒度地管理线程，从而实现更高效的线程并行协作”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [ThreadBlockTile协作组sync](thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《协作组简介》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [binary_partition](binary_partition.md)（`related`）：协作组简介明确把 binary_partition 列为按 0/1 标签划分父组的操作，后者给出 coalesced_group 返回值和 tile 大小约束。
- [coalesced_group简介](coalesced_group/coalesced_group_intro.md)（`related`）：coalesced_group 是协作组简介列出的 Warp 活跃线程子集，专页补充了分支发散和非独立线程调度约束。
- [grid_group简介](grid_group/grid_group_intro.md)（`related`）：grid_group 是简介列出的 Grid 全线程抽象，专页给出跨 block 查询与 sync 能力及纯 SIMT 限制。
- [协作组](cooperative_groups.md)（`same_topic`）：协作组汇总页与简介共同定义四类线程组、tiled/binary 划分和 sync 操作，并补充命名空间与头文件。
<!-- cannbot:related:end -->
