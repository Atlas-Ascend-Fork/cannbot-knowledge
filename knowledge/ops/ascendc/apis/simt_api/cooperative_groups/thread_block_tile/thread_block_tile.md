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
