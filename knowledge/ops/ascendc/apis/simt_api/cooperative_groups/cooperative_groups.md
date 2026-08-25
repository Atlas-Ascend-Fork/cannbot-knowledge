---
type: API
title: 协作组
description: SIMT API协作组类接口汇总，提供grid_group、thread_block、coalesced_group、thread_block_tile等线程组抽象与同步能力。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/cooperative_groups.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 协作组

cooperative_groups是Ascend C SIMT编程模型的拓展，用于组织协作线程组，实现更细粒度的线程并行协作。头文件为simt_api/cooperative_groups.h，所有API位于cooperative_groups命名空间下。
提供四种协作组类型：thread_block（线程块抽象）、coalesced_group（Warp活跃线程子集）、thread_block_tile（手动划分线程子组）、grid_group（Grid内所有线程抽象）。
划分操作含tiled_partition（按指定大小划分子组）和binary_partition（按0/1标签二分）。通用操作sync同步指定协作组内所有线程。grid_group仅支持SIMT编程场景，不支持SIMD与SIMT混合编程。
