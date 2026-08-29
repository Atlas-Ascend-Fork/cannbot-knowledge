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
